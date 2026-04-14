import os
import re
import json
import logging
import asyncio
import httpx
import PIL.Image
from typing import Optional, List, Union
from dotenv import load_dotenv
from google import genai
from google.genai import types

# 환경 변수 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("LLMService")

class LLMService:
    def __init__(self, model_name: str = "gemma4:latest"):
        self.provider = os.getenv("LLM_PROVIDER", "ollama").lower()
        
        # Ollama 설정
        self.ollama_url = "http://localhost:11434/api/generate"
        self.ollama_model = model_name
        
        # Google AI 설정
        self.google_api_key = os.getenv("GOOGLE_API_KEY")
        self.google_model = os.getenv("GOOGLE_MODEL_NAME", "models/gemma-4-31b")
        
        self.client = None
        if self.provider == "google" and self.google_api_key:
            try:
                self.client = genai.Client(api_key=self.google_api_key)
                logger.info(f"Gemma 4 엔진 초기화 완료 ({self.google_model})")
            except Exception as e:
                logger.error(f"Gemma 4 엔진 초기화 실패: {e}")
                self.provider = "ollama"
        
        if self.provider == "ollama":
            logger.info(f"Ollama 모드로 작동 중 ({self.ollama_model})")

    async def generate_response(self, user_mbti, target_mbti, situation, relationship, vibe, user_input):
        """상대방의 말에 대한 최적의 답변과 반응 예측 생성"""
        system_instruction = "너는 MBTI 전문가이자 심리 상담가야. 제공된 상황에 맞춰 상대방과 원활한 대화를 이끌어 나갈 수 있는 전략적 답변을 제안해."
        
        prompt = f"""
        [상황 정보]
        - 나의 MBTI: {user_mbti}
        - 상대방의 예상 MBTI: {target_mbti}
        - 대화 상황: {situation}
        - 관계 및 호감도: {relationship} (호감도: {vibe})
        
        [상대방의 메시지]
        "{user_input}"
        
        [지침]
        1. 수식 기호나 LaTeX 형식($...$)을 절대 사용하지 마십시오.
        2. 단계 구분 시 유니코드 기호(→, ➜, ✔)를 사용하십시오.
        3. {target_mbti} 성향 맞춤형 대화 리드법을 제시하십시오.
        4. 상대방이 보일 수 있는 구체적인 예상 반응(Reaction) 3가지를 예측하십시오.
        5. {user_mbti}로서 가장 자연스럽게 호감을 얻을 수 있는 조언을 포함하십시오.
        6. 바로 사용 가능한 답변 예시를 2-3개 작성하십시오.
        7. 답변은 마크다운 형식을 활용하되, 강조 기호(예: 강조)는 가독성을 해치므로 절대 사용하지 말고 줄바꿈과 유니코드 기호로만 문단을 구분하십시오.
        """

        return await self._call_llm(system_instruction, prompt)

    async def analyze_mbti_with_reasoning(self, context, user_input):
        """상황과 메시지를 분석하여 MBTI 추론"""
        system_instruction = "너는 예리한 심리학자이자 MBTI 분석 전문가야. 텍스트 단서를 바탕으로 성격 유형을 논리적으로 추론해."
        
        prompt = f"""
        [상세 상황 및 데이터]
        {context}
        
        [상대방의 메시지]
        "{user_input}"
        
        [지침]
        1. 제공된 [딥러닝 모델 측정값]이 있다면, 해당 수치를 심리학적으로 해석하십시오. (예: I 성향 80%라면 고립된 사고가 아닌 깊은 성찰의 특징으로 해석 등)
        2. {user_input} 문장에서 해당 MBTI와 일치하는 구체적인 언어적 단서(어미, 단어, 뉘앙스)를 찾아 분석하십시오.
        3. 최종적으로 가장 확률이 높은 단 하나의 MBTI 유형을 결론으로 내십시오.
        4. "데이터 분석 결과"와 "언어적 특징 근거" 섹션을 나누어 작성하십시오.
        5. 마크다운 형식을 사용하되, 강조를 위한 별표(**)는 절대 사용하지 마십시오.
        """
        
        return await self._call_llm(system_instruction, prompt)

    async def extract_text_from_image(self, image_input: Union[str, PIL.Image.Image]) -> str:
        """이미지(캡처본)에서 대화 텍스트 추출 (Gemma 4 Vision 활용)"""
        if self.provider != "google" or not self.client:
            return "OCR 기능은 Gemma 4 API 설정이 필요합니다."

        system_instruction = "너는 텍스트 추출 및 OCR 전문가야. 대화 캡처 이미지에서 대화 내용만 정확하게 추출해."
        prompt = "이미지 속의 대화 텍스트를 모두 추출해줘. 화자와 메시지 내용을 구분해서 출력해줘. 별도의 설명은 하지 말고 텍스트만 출력해."

        try:
            # 이미지 로드 (경로일 경우 PIL로 오픈)
            if isinstance(image_input, str):
                img = PIL.Image.open(image_input)
            else:
                img = image_input

            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.models.generate_content(
                    model=self.google_model,
                    contents=[img, prompt],
                    config={'system_instruction': system_instruction}
                )
            )
            return response.text.strip()
        except Exception as e:
            logger.error(f"Image OCR Error: {e}")
            return f"이미지 분석 중 오류가 발생했습니다: {str(e)}"

    async def simulate_reaction(self, user_mbti, target_mbti, situation, relationship, response_given):
        """제안된 답변을 보냈을 때 상대방(target_mbti)의 반응 시뮬레이션"""
        system_instruction = f"너는 {target_mbti} 성향을 가진 사람이야. 상대방의 메시지에 대해 너의 성격대로 반응해봐."
        
        prompt = f"""
        [상황 정보]
        - 나의 MBTI: {target_mbti} (분석된 성향)
        - 상대방의 MBTI: {user_mbti}
        - 우리 관계: {relationship}
        - 상황: {situation}
        
        [상대방이 보낸 메시지]
        "{response_given}"
        
        [지침]
        1. {target_mbti}의 전형적인 사고 방식과 말투로 응답하십시오.
        2. 속마음(생각)과 겉으로 하는 말(대화)을 구분해서 보여주십시오.
        3. 이 메시지를 받았을 때의 감정 변화를 유니코드 기호와 함께 간략히 적어주십시오.
        4. 마크다운 형식을 사용하되 강조 기호(**)는 사용하지 마십시오.
        """
        
        return await self._call_llm(system_instruction, prompt)

    async def chat_with_persona(self, history, user_input, user_mbti, target_mbti, relationship, situation):
        """특정 MBTI 페르소나와 대화 수행 (히스토리 포함)"""
        system_instruction = f"""
        너는 {target_mbti} 성향을 가진 사람이고, 상대방({user_mbti})과는 {relationship} 관계야.
        현재 상황은 {situation}이야.
        
        [지침]
        1. {target_mbti}의 전형적인 말투, 단어 선택, 반응 스타일을 완벽하게 모사해.
        2. 대화의 맥락(History)을 유지하며 자연스럽게 대화해.
        3. 너무 장황하거나 가르치려 들지 말고, 실제 메신저 대화처럼 간결하고 생동감 있게 대답해.
        4. 별표(**)와 같은 강조 기호는 가독성을 위해 절대 사용하지 마.
        5. 수식 기호나 LaTeX 형식($...$)을 사용하지 마.
        """

        if self.provider == "google" and self.client:
            try:
                # Gradio 6+ 히스토리(dict)를 처리하여 텍스트 컨텍스트로 변환
                full_context = ""
                for msg in history:
                    role = msg.get("role")
                    content = msg.get("content")
                    if role == "user":
                        full_context += f"사용자: {content}\n"
                    elif role == "assistant":
                        full_context += f"나({target_mbti}): {content}\n"
                
                prompt = f"{full_context}사용자: {user_input}\n나({target_mbti}):"
                
                return await self._generate_via_google(system_instruction, prompt)
            except Exception as e:
                logger.error(f"Chat Error: {e}")
                return "대화 중 오류가 발생했습니다."
        else:
            # Ollama용 히스토리 결합
            full_context = ""
            for msg in history:
                role = msg.get("role")
                content = msg.get("content")
                if role == "user":
                    full_context += f"User: {content}\n"
                elif role == "assistant":
                    full_context += f"Assistant: {content}\n"
            
            prompt = f"{system_instruction}\n\n{full_context}User: {user_input}\nAssistant:"
            return await self._generate_via_ollama(prompt)

            prompt = f"{system_instruction}\n\n{full_context}User: {user_input}\nAssistant:"
            return await self._generate_via_ollama(prompt)

    async def generate_initial_greeting(self, target_mbti, relationship, situation):
        """설정된 상황에 맞춰 AI가 건넬 첫 인사 생성"""
        system_instruction = f"너는 {target_mbti} 성향을 가진 사람이고, 상대방과는 {relationship} 관계야."
        prompt = f"현재 상황은 '{situation}'이야. 이 상황에서 {target_mbti}답게 상대방에게 건넬 수 있는 자연스러운 첫 인사나 말을 한 문장으로 해줘. 별도의 설명이나 인사말 없이 실제 대사만 출력해."
        return await self._call_llm(system_instruction, prompt)

    async def get_coaching_tip(self, user_input, target_mbti, relationship):
        """사용자 메시지에 대한 실시간 코칭 팁 생성"""
        system_instruction = "너는 세계 최고의 커뮤니케이션 전문가이자 심리 상담가야."
        prompt = f"""
        [대화 상황]
        사용자가 {target_mbti} 성향의 사람({relationship} 관계)에게 다음과 같은 메시지를 보냈어:
        "{user_input}"
        
        [분석 및 조언 지침]
        1. {target_mbti}의 성향을 고려할 때 이 메시지가 상대방에게 어떻게 느껴질지 예리하게 분석하십시오.
        2. 상대방의 호감을 얻거나 대화를 원활하게 이어가기 위한 구체적인 수정 제안이나 팁을 제시하십시오.
        3. 아주 정중하고 부드러운 전문 조언자 톤을 유지하십시오.
        4. 결과는 마크다운 형식을 사용하되, 강조 기호(**)는 절대 사용하지 마십시오. 유니코드 기호(➜, ✔)를 활용하십시오.
        """
        return await self._call_llm(system_instruction, prompt)

    async def _call_llm(self, system_text, user_text):
        """공통 LLM 호출 인터페이스 (비동기)"""
        if self.provider == "google" and self.client:
            return await self._generate_via_google(system_text, user_text)
        else:
            # Ollama는 시스템 프롬프트를 일반 프롬프트 앞에 결합하여 전송
            full_prompt = f"{system_text}\n\n{user_text}"
            return await self._generate_via_ollama(full_prompt)

    async def _generate_via_google(self, system_text, user_text):
        try:
            # Google SDK의 비동기 호출 (Thread 사용 혹은 직접 호출)
            # 현재 SDK 버전에 따라 동기 함수일 경우를 대비해 run_in_executor 사용 가능
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, 
                lambda: self.client.models.generate_content(
                    model=self.google_model,
                    contents=user_text,
                    config={'system_instruction': system_text}
                )
            )
            return self._clean_response(response.text)
        except Exception as e:
            logger.error(f"Gemma 4 호출 에러: {e}")
            return "서비스 일시 점검 중입니다. (Gemma 4 API Error)"

    async def _generate_via_ollama(self, prompt):
        payload = {
            "model": self.ollama_model,
            "prompt": prompt,
            "stream": False
        }
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(self.ollama_url, json=payload)
                response.raise_for_status()
                result = response.json().get('response', '')
                return self._clean_response(result)
        except Exception as e:
            logger.error(f"Ollama 호출 에러: {e}")
            return "로컬 엔진 연결에 실패했습니다. Ollama 실행 여부를 확인하세요."

    def _clean_response(self, text: str) -> str:
        """응답 데이터 정제 (Regex 활용)"""
        if not text:
            return ""

        # 1. 별표(**) 강조 기호 제거 (정규표현식)
        text = re.sub(r'\*\*', '', text)
        
        # 2. LaTeX 및 특수 기호 치환
        replacements = {
            r"\$\\rightarrow\$": " → ",
            r"\\rightarrow": " → ",
            r"\$\\leftarrow\$": " ← ",
            r"\\leftarrow": " ← ",
            r"\$\\Rightarrow\$": " ⇒ ",
            r"\\Rightarrow": " ⇒ ",
            r"\$\\checkmark\$": " ✔ ",
            r"\\checkmark": " ✔ ",
            r"\\text\{.*?\}": lambda m: m.group(0)[6:-1], # \text{내용} -> 내용
            r"\\": "" # 남은 백슬래시 제거
        }
        
        for pattern, replacement in replacements.items():
            if callable(replacement):
                text = re.sub(pattern, replacement, text)
            else:
                text = text.replace(pattern.replace("\\", ""), replacement) if "\\" in pattern else text.replace(pattern, replacement)
                # 단순 replace 보완을 위해 다시 한번 처리
                text = re.sub(pattern, replacement, text)

        return text.strip()
