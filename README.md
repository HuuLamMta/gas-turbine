# Phần mềm tính chu trình nhiệt động cơ tua bin khí

Ứng dụng web phục vụ học tập, phân tích kỹ thuật và thiết kế sơ bộ chu trình
Brayton hở một trục. Lõi tính toán tách khỏi giao diện, dùng SI và kiểm tra các
điều kiện vật lý trước khi trả kết quả.

## Chức năng

- Chu trình Brayton không lý tưởng với tổn thất cửa vào, buồng đốt và đường xả.
- Cân bằng năng lượng nhiên liệu–không khí và công trục.
- Bảng trạng thái tại trạm 1–4, hiệu suất nhiệt, SFC, công suất trục/điện.
- Biểu đồ nhiệt độ, T–s gần đúng và cân bằng công.
- Mô phỏng SVG động của dòng khí, máy nén, buồng đốt, rotor tua bin và máy phát.
- Quét tỷ số nén để khảo sát hiệu suất và công riêng.
- Xuất bảng trạng thái CSV.
- Kiểm thử công thức thành phần, cân bằng năng lượng và ca hồi quy hoàn chỉnh.

## Cài đặt và chạy trên Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pip install -e .
streamlit run app.py
```

Nếu PowerShell chặn script kích hoạt, không cần thay đổi chính sách hệ thống:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Chạy kiểm thử:

```powershell
.\.venv\Scripts\python.exe -m pytest
```

## Mô hình và công thức chính

Máy nén:

```text
T2s = T1 × πc^((γa − 1)/γa)
T2  = T1 + (T2s − T1)/ηc
wc  = cp,a × (T2 − T1)
```

Buồng đốt:

```text
P3 = P2 × (1 − ΔPb)
f  = cp,g × (T3 − T2) / (ηb × LHV − cp,g × T3)
```

Tua bin và công hữu ích:

```text
T4s   = T3 × (P4/P3)^((γg − 1)/γg)
T4    = T3 − ηt × (T3 − T4s)
wt,a  = (1 + f) × cp,g × (T3 − T4)
wnet  = ηm × wt,a − wc
ηth   = wnet / (f × LHV)
SFC   = f/wnet × 3 600 000
```

## Giả thiết và giới hạn

- Dòng ổn định, khí lý tưởng, `cp` và `γ` không đổi.
- Cháy hoàn toàn; không xét phân ly, phát thải hay cân bằng hóa học.
- Không có bản đồ đặc tính, chế độ ngoài thiết kế hoặc quá độ.
- Sơ đồ T–s là gần đúng, không thay thế thư viện tính chất nhiệt thực.

Phần mềm không được chứng nhận cho vận hành, điều khiển hoặc thiết kế an toàn
động cơ thực. Thiết kế chi tiết cần dữ liệu thử nghiệm, bản đồ nhà sản xuất,
biên an toàn và thẩm định của chuyên gia.
