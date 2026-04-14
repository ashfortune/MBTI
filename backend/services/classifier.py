import tensorflow as tf
import re
import numpy as np
import os
from dotenv import load_dotenv
from transformers import AutoTokenizer, TFDistilBertForSequenceClassification

# .env 파일 활성화
load_dotenv()

class MBTIClassifier:
    def __init__(self):
        # 환경 변수에서 경로 가져오기 (기본값은 HF 저장소 ID)
        self.base_path = os.getenv("MODEL_PATH", "ashfortune/communiKate")
        
        # 해당 경로가 실제 로컬 폴더인지 확인
        self.is_local = os.path.isdir(self.base_path)
        self.version_folder = "bert_mbti_ver2"

        mode_str = "LOCAL" if self.is_local else "HUGGINGFACE HUB"
        print(f"DEBUG: [{mode_str} MODE] 엔진 가동 중... ({self.base_path})")
        
        self.axis_map = {'ie': 'mbti_model_ie', 'ns': 'mbti_model_ns', 'tf': 'mbti_model_tf', 'jp': 'mbti_model_jp'}
        self.model_names = list(self.axis_map.keys())
        self.models = {}
        
        # 1. 토크나이저 로드
        first_sub = self.axis_map[self.model_names[0]]
        
        if self.is_local:
            # 로컬 경로 처리
            self.tokenizer = AutoTokenizer.from_pretrained(os.path.join(self.base_path, first_sub))
        else:
            # [수정] 배포 경로: 직접 슬래시(/)로 연결하여 경로 명시
            hf_subfolder = f"{self.version_folder}/{first_sub}"
            self.tokenizer = AutoTokenizer.from_pretrained(self.base_path, subfolder=hf_subfolder)
        
        # 2. 4개의 독립 모델 로드
        for name, subfolder in self.axis_map.items():
            print(f"DEBUG: '{name.upper()}' 전문 모델 로딩 중...")
            
            if self.is_local:
                model_full_path = os.path.join(self.base_path, subfolder)
                self.models[name] = TFDistilBertForSequenceClassification.from_pretrained(model_full_path)
            else:
                # [수정] use_safetensors=True 옵션 추가 및 경로 문자열 처리
                hf_subfolder = f"{self.version_folder}/{subfolder}"
                self.models[name] = TFDistilBertForSequenceClassification.from_pretrained(
                    self.base_path, 
                    subfolder=hf_subfolder, 
                    from_pt=True,         # PyTorch 가중치 변환
                    use_safetensors=True  # [추가] safetensors 파일 우선 사용
                )
            
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
        inputs = self.tokenizer(
            [cleaned], 
            truncation=True, 
            padding=True, 
            max_length=256, 
            return_tensors="tf"
        )
        
        axis_probs = {}
        result_mbti = ""
        
        for name in self.model_names:
            filtered_inputs = {k: v for k, v in inputs.items() if k != 'token_type_ids'}
            outputs = self.models[name](filtered_inputs)
            probs = tf.nn.softmax(outputs.logits, axis=-1).numpy()[0]
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