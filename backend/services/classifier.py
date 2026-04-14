import re
import numpy as np
import os
import torch  # [수정] TensorFlow 대신 PyTorch 사용
from dotenv import load_dotenv
from transformers import AutoTokenizer, AutoModelForSequenceClassification # [수정] TF 제거된 만능 클래스
from huggingface_hub import snapshot_download

# .env 파일 활성화
load_dotenv()

class MBTIClassifier:
    def __init__(self):
        self.repo_id = os.getenv("MODEL_PATH", "ashfortune/communiKate")
        self.version_folder = "bert_mbti_ver2"
        
        # 1. 모델 강제 다운로드 (경로 에러 완벽 차단)
        if not os.path.isdir(self.repo_id):
            print(f"DEBUG: [HUGGINGFACE HUB] 모델 파일을 서버로 강제 다운로드 합니다... ({self.repo_id})")
            local_download_path = snapshot_download(repo_id=self.repo_id, repo_type="model")
            self.base_path = os.path.join(local_download_path, self.version_folder)
        else:
            print(f"DEBUG: [LOCAL] 내 컴퓨터의 모델을 사용합니다.")
            self.base_path = self.repo_id if self.version_folder in self.repo_id else os.path.join(self.repo_id, self.version_folder)

        print(f"DEBUG: 최종 로드 경로 -> {self.base_path}")
        
        self.axis_map = {'ie': 'mbti_model_ie', 'ns': 'mbti_model_ns', 'tf': 'mbti_model_tf', 'jp': 'mbti_model_jp'}
        self.model_names = list(self.axis_map.keys())
        self.models = {}
        
        # 2. 토크나이저 로드
        first_sub = self.axis_map[self.model_names[0]]
        tokenizer_path = os.path.join(self.base_path, first_sub)
        print(f"DEBUG: 토크나이저 로딩 중... ({tokenizer_path})")
        self.tokenizer = AutoTokenizer.from_pretrained(tokenizer_path)
        
        # 3. 4개의 독립 모델 로드 (PyTorch 클래스로 로드)
        for name, subfolder in self.axis_map.items():
            model_full_path = os.path.join(self.base_path, subfolder)
            print(f"DEBUG: '{name.upper()}' 전문 모델 로딩 중... ({model_full_path})")
            
            # [수정] TF 떼고, from_pt=True 옵션도 뺐습니다. (원래 자기 포맷이니까요!)
            self.models[name] = AutoModelForSequenceClassification.from_pretrained(
                model_full_path, 
                use_safetensors=True
            )
            # 예측 속도 향상을 위해 모델을 평가(Evaluation) 모드로 설정
            self.models[name].eval()
            
        self.labels = {'ie': ['E', 'I'], 'ns': ['N', 'S'], 'tf': ['F', 'T'], 'jp': ['J', 'P']}
        self.all_types = [
            'ENFJ', 'ENFP', 'ENTJ', 'ENTP', 'ESFJ', 'ESFP', 'ESTJ', 'ESTP',
            'INFJ', 'INFP', 'INTJ', 'INTP', 'ISFJ', 'ISFP', 'ISTJ', 'ISTP'
        ]

    def _clean_text(self, text):
        text = text.lower()
        text = re.sub(r'http\S+|www.\S+', '', text)
        return text

    def predict(self, text):
        cleaned = self._clean_text(text)
        # [수정] return_tensors를 'tf'에서 'pt'(PyTorch)로 변경
        inputs = self.tokenizer(
            [cleaned], 
            truncation=True, 
            padding=True, 
            max_length=256, 
            return_tensors="pt" 
        )
        
        axis_probs = {}
        result_mbti = ""
        
        for name in self.model_names:
            filtered_inputs = {k: v for k, v in inputs.items() if k != 'token_type_ids'}
            
            # [수정] PyTorch 방식으로 예측 실행 및 확률(Softmax) 계산
            with torch.no_grad(): # 메모리 절약
                outputs = self.models[name](**filtered_inputs)
                
            probs = torch.nn.functional.softmax(outputs.logits, dim=-1)[0].numpy()
            axis_probs[name] = probs
            
            best_idx = np.argmax(probs)
            result_mbti += self.labels[name][best_idx]
            
        full_probabilities = {}
        for mbti in self.all_types:
            p_ie = axis_probs['ie'][0 if mbti[0]=='E' else 1]
            p_ns = axis_probs['ns'][0 if mbti[1]=='N' else 1]
            p_tf = axis_probs['tf'][0 if mbti[2]=='F' else 1]
            p_jp = axis_probs['jp'][0 if mbti[3]=='J' else 1]
            
            full_probabilities[mbti] = float(p_ie * p_ns * p_tf * p_jp)
            
        confidence = full_probabilities[result_mbti]
        
        return {
            "mbti": result_mbti,
            "confidence": confidence,
            "probabilities": full_probabilities
        }