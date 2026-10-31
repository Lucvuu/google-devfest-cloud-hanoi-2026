"""
DevFest Cloud Hanoi 2026 - Spatial AI with Gemini Flash & Structured Output
Speaker: Ms. Nguyen Khanh Linh (Obello / GDE AI/ML)
"""

import os
from typing import List
from pydantic import BaseModel, Field

# Khai báo schema chuẩn hóa cho các đối tượng không gian được nhận diện
class BoundingBox(BaseModel):
    label: str = Field(description="Tên hoặc phân loại của đối tượng nhận diện")
    box_2d: List[int] = Field(
        description="Tọa độ hộp bao chuẩn hóa [ymin, xmin, ymax, xmax] trong thang đo 0-1000"
    )
    confidence_reasoning: str = Field(
        description="Lý do hoặc mô tả ngắn gọn về vị trí của đối tượng trong bức ảnh"
    )

class SpatialDetectionResult(BaseModel):
    image_summary: str = Field(description="Mô tả bối cảnh tổng quan của bức ảnh")
    objects: List[BoundingBox] = Field(description="Danh sách các đối tượng kèm tọa độ không gian")


def run_spatial_detection_example():
    """Ví dụ gọi Gemini nhận diện không gian (Spatial AI) với structured output."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key or api_key == "YOUR_GEMINI_API_KEY_HERE":
        print("⚠️ Chưa cấu hình GOOGLE_API_KEY. Vui lòng thiết lập biến môi trường để chạy với Gemini API thật.")
        print("\nVí dụ kết quả mẫu mà Gemini 3.8 Flash sẽ trả về:")
        mock_result = SpatialDetectionResult(
            image_summary="Khung cảnh phòng làm việc công nghệ cao với laptop và cốc cà phê trên bàn.",
            objects=[
                BoundingBox(label="laptop", box_2d=[350, 200, 750, 700], confidence_reasoning="Nằm ở trung tâm của mặt bàn"),
                BoundingBox(label="coffee_cup", box_2d=[500, 750, 680, 880], confidence_reasoning="Đặt ở góc phải bàn làm việc"),
                BoundingBox(label="smartphone", box_2d=[580, 120, 720, 250], confidence_reasoning="Nằm cạnh mép bàn bên trái")
            ]
        )
        print(mock_result.model_dump_json(indent=2))
        return

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)
        
        prompt = (
            "Analyze the image and detect prominent objects. "
            "Return spatial bounding boxes [ymin, xmin, ymax, xmax] scaled 0-1000."
        )
        
        # Với ảnh mẫu, bạn có thể truyền types.Part.from_bytes() hoặc PIL.Image
        print("Đang gọi Gemini Flash với Spatial AI configuration...")
        # response = client.models.generate_content(...)
    except Exception as e:
        print(f"Lỗi: {e}")


if __name__ == "__main__":
    run_spatial_detection_example()

