import tensorflow as tf
import re
import numpy as np
import os
from dotenv import load_dotenv
from transformers import AutoTokenizer, TFAutoModelForSequenceClassification
from huggingface_hub import snapshot_download

# .env 파일 활성화
load_dotenv()

class MBTIClassifier:
    def __init__(self):
        self.repo_id = os.getenv("MODEL_PATH", "ashfortune/communiKate")
        self.version_folder = "bert_mbti_ver2"
        
        # 1. 모델 강제 다운로드 (핵심)
        # 만약 진짜 내 컴퓨터(Mac)라면 다운로드하지 않고 넘어갑니다.
        if not os.path.isdir(self.repo_id):
            print(f"DEBUG: [HUGGINGFACE HUB] 모델 파일을 서버로 강제 다운로드 합니다... ({self.repo_id})")
            # 저장소 전체를 다운로드하고, 그 임시 로컬 경로를 반환받습니다.
            local_download_path = snapshot_download(repo_id=self.repo_id, repo_type="model")
            self.base_path = os.path.join(local_download_path, self.version_folder)
        else:
            print(f"DEBUG: [LOCAL] 내 컴퓨터의 모델을 사용합니다.")
            self.base_path = self.repo_id if self.version_folder in self.repo_id else os.path.join(self.repo_id, self.version_folder)

        print(f"DEBUG: 최종 로드 경로 -> {self.base_path}")
        
        self.axis_map = {'ie': 'mbti_model_ie', 'ns': 'mbti_model_ns', 'tf': 'mbti_model_tf', 'jp': 'mbti_model_jp'}
        self.model_names = list(self.axis_map.keys())
        self.models = {}
        
        # 2. 토크나이저 로드 (이제 무조건 로컬 폴더에서 읽음)
        first_sub = self.axis_map[self.model_names[0]]
        tokenizer_path = os.path.join(self.base_path, first_sub)
        print(f"DEBUG: 토크나이저 로딩 중... ({tokenizer_path})")
        self.tokenizer = AutoTokenizer.from_pretrained(tokenizer_path)
        
        # 3. 4개의 독립 모델 로드 (이제 무조건 로컬 폴더에서 읽음)
        for name, subfolder in self.axis_map.items():
            model_full_path = os.path.join(self.base_path, subfolder)
            print(f"DEBUG: '{name.upper()}' 전문 모델 로딩 중... ({model_full_path})")
            
            # 서버 하드디스크에서 바로 읽으므로 경로 오류가 날 수 없습니다.
            self.models[name] = TFAutoModelForSequenceClassification.from_pretrained(
                model_full_path, 
                from_pt=True,
                use_safetensors=True
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