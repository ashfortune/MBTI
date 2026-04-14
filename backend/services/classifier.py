import tensorflow as tf
import re
import numpy as np
import os
from transformers import AutoTokenizer, TFDistilBertForSequenceClassification

class MBTIClassifier:
    def __init__(self, base_model_dir):
        """
        4개 바이너리 모델을 통합한 하이브리드 MBTI 분류기
        :param base_model_dir: 4개 모델 폴더(ie, ns, tf, jp)가 들어있는 최상위 디렉토리
        """
        print(f"DEBUG: 하이브리드 엔진 통합 가동 중... ({base_model_dir})")
        
        # 4개 지표 모델 폴더명 정의
        self.axis_map = {
            'ie': 'mbti_model_ie',
            'ns': 'mbti_model_ns',
            'tf': 'mbti_model_tf',
            'jp': 'mbti_model_jp'
        }
        self.model_names = list(self.axis_map.keys())
        self.models = {}
        
        # 1. 토크나이저는 하나만 로드하여 공유 (메모리 최적화)
        # 첫 번째 모델 폴더에서 토크나이저 로드
        first_model_path = os.path.join(base_model_dir, self.axis_map[self.model_names[0]])
        self.tokenizer = AutoTokenizer.from_pretrained(first_model_path)
        
        # 2. 4개의 독립 모델 로드
        for name, folder in self.axis_map.items():
            model_path = os.path.join(base_model_dir, folder)
            print(f"DEBUG: '{name.upper()}' 전문 모델 로딩... ({model_path})")
            # Safetensors(PyTorch) 모델을 TF로 로드하기 위해 from_pt=True 적용
            self.models[name] = TFDistilBertForSequenceClassification.from_pretrained(model_path, from_pt=True)
            
        # 3. 지표별 라벨 매핑 (알파벳 순서: 0=Primary, 1=Secondary)
        # E:0, I:1 / N:0, S:1 / F:0, T:1 / J:0, P:1
        self.labels = {
            'ie': ['E', 'I'],
            'ns': ['N', 'S'],
            'tf': ['F', 'T'],
            'jp': ['J', 'P']
        }
        
        # 4. 전체 16가지 유형 리스트 (합성용)
        self.all_types = [
            'ENFJ', 'ENFP', 'ENTJ', 'ENTP', 'ESFJ', 'ESFP', 'ESTJ', 'ESTP',
            'INFJ', 'INFP', 'INTJ', 'INTP', 'ISFJ', 'ISFP', 'ISTJ', 'ISTP'
        ]

    def _clean_text(self, text):
        # 텍스트 전처리: 소문자화 및 URL 제거 등
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
        
        # 1. 4개 모델 각각 예측 수행 및 확률 추출
        axis_probs = {}
        result_mbti = ""
        
        for name in self.model_names:
            # DistilBERT는 token_type_ids를 지원하지 않으므로 필터링 후 전달
            filtered_inputs = {k: v for k, v in inputs.items() if k != 'token_type_ids'}
            outputs = self.models[name](filtered_inputs)
            # Softmax를 통해 해당 축의 확률 계산 (예: [P(E), P(I)])
            # [[logit_0, logit_1]] -> softmax -> [[p_0, p_1]]
            probs = tf.nn.softmax(outputs.logits, axis=-1).numpy()[0]
            axis_probs[name] = probs
            
            # 더 높은 확률의 문자를 결과에 추가
            best_idx = np.argmax(probs)
            result_mbti += self.labels[name][best_idx]
            
        # 2. 16유형 확률 합성 (Probabilistic Synthesis)
        # 개별 축의 확률이 독립적이라고 가정하고 곱함
        # P(MBTI) = P(Axis1) * P(Axis2) * P(Axis3) * P(Axis4)
        full_probabilities = {}
        for mbti in self.all_types:
            # 각 자리 문자에 해당하는 확률을 찾아 곱함
            p_ie = axis_probs['ie'][0 if mbti[0]=='E' else 1]
            p_ns = axis_probs['ns'][0 if mbti[1]=='N' else 1]
            p_tf = axis_probs['tf'][0 if mbti[2]=='F' else 1]
            p_jp = axis_probs['jp'][0 if mbti[3]=='J' else 1]
            
            full_probabilities[mbti] = float(p_ie * p_ns * p_tf * p_jp)
            
        # 3. 최종 신뢰도 (조합된 결과의 확률)
        confidence = full_probabilities[result_mbti]
        
        return {
            "mbti": result_mbti,
            "confidence": confidence,
            "probabilities": full_probabilities
        }