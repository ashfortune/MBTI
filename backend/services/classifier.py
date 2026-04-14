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
        """
        환경 변수 MODEL_PATH를 읽어 로컬 폴더 또는 HF Hub에서 모델을 자동 로드합니다.
        """
        # 환경 변수에서 경로 가져오기 (기본값은 HF 저장소 ID)
        self.base_path = os.getenv("MODEL_PATH", "ashfortune/communiKate")
        
        # 해당 경로가 실제 로컬 폴더인지 확인
        self.is_local = os.path.isdir(self.base_path)
        
        # [수정] 웹 배포 시 저장소 내부의 중간 폴더 경로 설정
        # 로컬 폴더 경로(예: ./models/bert_mbti_ver2)에 이미 버전 폴더가 포함되어 있다면 로컬에선 무시합니다.
        self.version_folder = "bert_mbti_ver2"

        mode_str = "LOCAL" if self.is_local else "HUGGINGFACE HUB"
        print(f"DEBUG: [{mode_str} MODE] 엔진 가동 중... ({self.base_path})")
        
        self.axis_map = {
            'ie': 'mbti_model_ie',
            'ns': 'mbti_model_ns',
            'tf': 'mbti_model_tf',
            'jp': 'mbti_model_jp'
        }
        self.model_names = list(self.axis_map.keys())
        self.models = {}
        
        # 1. 토크나이저 로드 (첫 번째 모델 폴더 기준)
        first_sub = self.axis_map[self.model_names[0]]
        print(f"DEBUG: 토크나이저 로딩 중...")
        
        if self.is_local:
            # 로컬: ./models/bert_mbti_ver2/mbti_model_ie
            self.tokenizer = AutoTokenizer.from_pretrained(os.path.join(self.base_path, first_sub))
        else:
            # [수정] 배포: ashfortune/communiKate 안의 'bert_mbti_ver2/mbti_model_ie'
            hf_subfolder = os.path.join(self.version_folder, first_sub)
            self.tokenizer = AutoTokenizer.from_pretrained(self.base_path, subfolder=hf_subfolder)
        
        # 2. 4개의 독립 모델 로드
        for name, subfolder in self.axis_map.items():
            print(f"DEBUG: '{name.upper()}' 전문 모델 로딩 중...")
            
            if self.is_local:
                # [로컬 모드]
                model_full_path = os.path.join(self.base_path, subfolder)
                self.models[name] = TFDistilBertForSequenceClassification.from_pretrained(model_full_path)
            else:
                # [수정] [배포 모드] 중간 폴더(bert_mbti_ver2)를 경로에 추가
                hf_subfolder = os.path.join(self.version_folder, subfolder)
                self.models[name] = TFDistilBertForSequenceClassification.from_pretrained(
                    self.base_path, 
                    subfolder=hf_subfolder, 
                    from_pt=True # PyTorch 가중치 변환 허용
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