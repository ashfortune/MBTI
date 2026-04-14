const getApiBaseUrl = () => {
  let url = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  
  // 끝부분의 슬래시(/) 제거
  url = url.replace(/\/+$/, "");
  
  // url에 /api가 포함되어 있지 않다면 추가 (단, 비어있지 않은 경우에만)
  if (url && !url.endsWith("/api")) {
    url = `${url}/api`;
  }
  
  return url;
};

const API_BASE_URL = getApiBaseUrl();

export async function post(endpoint: string, data: any) {
  // endpoint가 /로 시작하지 않으면 추가
  const path = endpoint.startsWith("/") ? endpoint : `/${endpoint}`;
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Something went wrong");
  }
  return response.json();
}

export async function uploadImage(file: File) {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE_URL}/ocr`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    throw new Error("OCR failed");
  }

  return response.json();
}
