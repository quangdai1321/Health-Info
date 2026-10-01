# Hệ thống LLM có ràng buộc theo luật để diễn giải kết quả xét nghiệm máu cho bệnh nhân Việt Nam

> **Đây là bản dịch tiếng Việt để bạn đọc và rà soát nội dung.**
> Bản nộp hội nghị là `manuscript.tex` (tiếng Anh). Hai bản phải khớp nhau về
> nội dung — nếu bạn sửa bản tiếng Anh thì nhớ sửa cả bản này.

---

## Tóm tắt (Abstract)

Bệnh nhân ở Việt Nam thường xuyên nhận phiếu xét nghiệm viết bằng thuật ngữ
lâm sàng mà họ không hiểu, và ngày càng tìm đến các mô hình ngôn ngữ phổ thông
để được giải thích. Chúng tôi cho thấy điều này không an toàn: một mô hình
không có ràng buộc, khi được yêu cầu giải thích các phiếu công thức máu tổng
hợp, đã nói sai chiều lệch của chỉ số ở **91,3%** số ca, và nói với bệnh nhân
có kết quả bất thường rằng mọi thứ đều bình thường ở **32,0%** số ca.

Chúng tôi đề xuất một quy trình bốn tầng, trong đó mọi phán đoán lâm sàng đều
do luật xác định trước khi mô hình ngôn ngữ được gọi; mô hình chỉ diễn đạt lại
các nhãn đã gán sẵn, và một bộ kiểm chứng sau sinh sẽ loại bỏ những đầu ra mâu
thuẫn với nhãn đó. Trên 150 phiếu tổng hợp, quy trình đầy đủ **không tạo ra
đầu ra không an toàn nào**, trong đó 64,0% do mô hình sinh và 36,0% rơi về bản
mẫu cố định. Hệ thống chạy được trên CPU, không cần GPU.

**Từ khóa:** năng lực hiểu biết sức khỏe, mô hình ngôn ngữ lớn, kết quả xét
nghiệm, giao tiếp với bệnh nhân, an toàn AI

---

## 1. Giới thiệu

Một bệnh nhân rời phòng xét nghiệm ở Việt Nam cầm trên tay một bảng số kèm các
thuật ngữ như `PDW`, `MCHC`, `Monocyte`, với đơn vị `G/L`, `fL`, `pg`. Khoảng
tham chiếu được in bên cạnh mỗi giá trị nên người bệnh thấy được con số nào
nằm ngoài khoảng, nhưng không biết chỉ số đó đo cái gì, mức lệch có đáng ngại
không, và cần làm gì tiếp theo. Khoảng cách giữa việc có kết quả và việc hiểu
kết quả chính là điều mà khái niệm năng lực hiểu biết sức khỏe (health
literacy) mô tả: khả năng tiếp cận, hiểu, đánh giá và sử dụng thông tin y tế
để tự chăm sóc sức khỏe của mình.

Việc bệnh nhân bị bỏ mặc tự xoay xở với khoảng cách này đã được ghi nhận
trong một nghiên cứu trên 93 bệnh nhân nhận kết quả qua cổng thông tin trực
tuyến [1]: gần **hai phần ba không được giải thích gì** về kết quả, và **46%
phải tự tra cứu trên mạng** để hiểu. Ngày nay, việc tra cứu đó thường có
nghĩa là chụp ảnh phiếu xét nghiệm rồi hỏi một mô hình ngôn ngữ phổ thông.

Kiểu thất bại này rất dễ tái hiện. Khi được hỏi bằng tiếng Việt bạch cầu là
gì, mô hình 3 tỷ tham số dùng trong nghiên cứu này trả lời rằng bạch cầu là
tế bào lympho, trong khi lympho chỉ là một loại bạch cầu chứ không phải từ
đồng nghĩa, rồi tự ý nhắc đến ung thư và suy giảm miễn dịch. Một người cầm
kết quả hoàn toàn bình thường sẽ gặp một lỗi định nghĩa và hai căn bệnh đáng
sợ chỉ trong một câu trả lời ngắn.

Kiểu thất bại nghiêm trọng hơn lại đi theo chiều ngược lại. Một mô hình tóm
tắt rằng phiếu bình thường trong khi nó không bình thường thì không chỉ đưa
thông tin sai, mà còn triệt tiêu lý do đi khám. Lỗi thuật ngữ thì người đọc
nhìn thấy được và có động cơ đi kiểm chứng; còn trấn an sai thì trôi chảy, dễ
chịu, và tác động bằng cách khiến người ta không hành động. Vì vậy chúng tôi
tách nó thành một loại lỗi riêng và đo riêng.

Quan điểm của chúng tôi là không nên giao nhiệm vụ cho mô hình theo cách
người ta vẫn giao. Xác định một giá trị có bất thường hay không là phép so
sánh số học với khoảng tham chiếu, và một chương trình làm việc đó chính xác
tuyệt đối; còn diễn đạt kết luận ấy bằng ngôn ngữ đời thường mới là việc mô
hình ngôn ngữ làm tốt. Tách hai việc ra, rồi kiểm chứng việc thứ hai dựa trên
việc thứ nhất, sẽ loại bỏ kiểu thất bại thay vì chỉ dặn dò cho nó biến mất.

### Đóng góp của bài báo

1. **Quy trình bốn tầng** trong đó mọi phán đoán lâm sàng được hoàn tất bằng
   luật trước khi sinh văn bản, nên mô hình diễn đạt lại các nhãn có sẵn chứ
   không tự suy ra.
2. **Bộ kiểm chứng tự động sau sinh**, đối chiếu văn bản sinh ra với các nhãn
   đó và rơi về bản mẫu cố định khi không khớp, đảm bảo không có văn bản chưa
   kiểm chứng nào đến tay người đọc.
3. **Đánh giá trên 150 phiếu công thức máu tổng hợp**, đo sáu loại lỗi, trong
   đó có trấn an sai. Theo hiểu biết của chúng tôi, chỉ số này chưa từng được
   báo cáo riêng trong các nghiên cứu trước về diễn giải kết quả cho bệnh
   nhân.
4. **Ghi nhận vấn đề đơn vị không đồng nhất** giữa các phòng xét nghiệm Việt
   Nam, gây phân loại sai nghiêm trọng ngay trong tầng luật nếu không chuẩn
   hóa tường minh.

Hệ thống chạy trên máy tính thông thường không cần GPU: dữ liệu xét nghiệm
không phải rời khỏi cơ sở y tế, và bệnh viện tuyến tỉnh không phải mua card đồ
họa để dùng.

---

## 2. Các nghiên cứu liên quan

### 2.1. Mô hình ngôn ngữ diễn giải kết quả cho bệnh nhân

Nghiên cứu gần nhất với bài này đánh giá xem các mô hình phổ thông có trả lời
được câu hỏi của bệnh nhân về kết quả xét nghiệm hay không. He và cộng sự [2]
so sánh câu trả lời của mô hình với câu trả lời của người dùng khác trên 53
cặp hỏi đáp lấy từ một diễn đàn, đánh giá theo bốn tiêu chí: liên quan, chính
xác, hữu ích và mức độ gây hại; GPT-4 vượt trội so với các mô hình mã nguồn mở
nhỏ hơn. Bozer và Pekçevik [3] làm việc tương tự trong lĩnh vực chẩn đoán hình
ảnh, đo độ dễ đọc, độ dễ hiểu, cách dùng ngôn ngữ thể hiện sự không chắc chắn,
và khả năng gây lo lắng trên nhiều mô hình. Ở hướng gần với bệnh nhân hơn,
Kianian và cộng sự [4] khảo sát khả năng mô hình ngôn ngữ giúp người bệnh hiểu
các bài báo khoa học về nhãn khoa.

Các đánh giá từ chính giới xét nghiệm y học lại thận trọng hơn. Nhóm công tác
về trí tuệ nhân tạo của Liên đoàn Hóa sinh Lâm sàng và Y học Xét nghiệm châu
Âu (EFLM) [5] kết luận rằng các mô hình này có thể đưa ra câu trả lời hời hợt
hoặc sai về kết quả xét nghiệm, và không thể dùng cho mục đích chẩn đoán. Trên
30 câu hỏi diễn giải do bác sĩ đặt ra, GPT-4 trả lời đúng 46,7%, đúng một phần
23,3%, và sai hoặc lạc đề 30% [6]. Những đánh giá này nhắm vào người dùng là
bác sĩ; trường hợp người dùng là bệnh nhân còn rủi ro hơn, vì họ ít có cơ sở
để nhận ra một câu trả lời sai.

**Khoảng trống nghiên cứu.** Các nghiên cứu trên hướng tới độ dễ đọc và
độ chính xác chung. Mức độ gây hại, nếu có đo, cũng chỉ là một chiều trong
nhiều chiều chứ không được phân tách thành từng kiểu thất bại cụ thể, và
chúng tôi chưa thấy công trình nào tách riêng trấn an sai. Ngoài ra, các
nghiên cứu này đánh giá mô hình dùng trực tiếp, không có cơ chế trung gian
nào ngăn một câu trả lời không an toàn đến tay người đọc. Đóng góp của chúng
tôi mang tính kiến trúc chứ không phải đánh giá: câu hỏi không phải là mô
hình làm tốt đến đâu, mà là bố trí hệ thống thế nào để thất bại của nó không
lan ra.

### 2.2. Năng lực hiểu biết sức khỏe ở Việt Nam

Tiền đề rằng bệnh nhân không tự đọc hiểu được phiếu xét nghiệm có cơ sở vững ở
Việt Nam. Một nghiên cứu cắt ngang trên 204 người cao tuổi tại Đà Nẵng [7] ghi
nhận 60,3% có năng lực hiểu biết sức khỏe chung không đầy đủ; người ở đô thị
cao gấp 2,4 lần người ở nông thôn, và trình độ học vấn là yếu tố quyết định
mạnh. Các nghiên cứu trước trên người cao tuổi Việt Nam [8] và nghiên cứu
kiểm định thang đo năng lực hiểu biết sức khỏe trên người bệnh mạn tính [9]
cho kết quả tương tự.

Một khảo sát quốc gia gần đây [10] cho thấy một kết hợp đặc biệt liên quan đến
bài này: eHealth literacy cao đi cùng health literacy chung thấp ở người
trưởng thành có kết nối số, với hành vi tìm kiếm thông tin sức khỏe trực tuyến
rất phổ biến. Nói cách khác, người dân vừa sẵn sàng vừa có khả năng dùng công cụ
trực tuyến, nhưng lại kém trang bị hơn để đánh giá thứ mà công cụ đó nói với
họ. Điều đó làm tăng, chứ không giảm, yêu cầu an toàn đặt lên các công cụ ấy.

### 2.3. Ràng buộc và kiểm chứng đầu ra mô hình

Giải mã có ràng buộc văn phạm (grammar-constrained decoding) [11], [12] hạn
chế phân bố token ở mỗi bước sao cho chỉ những chuỗi tuân theo văn phạm mới
sinh ra được, và sinh văn bản theo schema nay đã là giao diện chuẩn để lấy đầu
ra máy đọc được. Hướng liên quan là giải mã có ràng buộc tri thức kèm phát
hiện ảo giác ở mức token [13].

Tuy nhiên, hợp lệ về cấu trúc không đồng nghĩa với đúng về ngữ nghĩa: một
phản hồi có thể thỏa mãn schema hoàn hảo mà vẫn chứa giá trị sai so với đầu
vào. Tầng 4 của chúng tôi hoạt động ở tầng nghĩa thứ hai này. Nó không kiểm
tra đầu ra có phân tích cú pháp được không, vì ràng buộc schema đã lo việc
đó, mà kiểm tra nội dung có khớp với các nhãn được tính độc lập với mô hình
hay không. Việc này gần với kiểm chứng dựa trên nguồn sự thật bên ngoài hơn
là giải mã có ràng buộc, và hai cách bổ trợ cho nhau: chúng tôi áp ràng buộc
schema lúc sinh, và kiểm chứng ngữ nghĩa sau khi sinh.

### 2.4. Chuẩn hóa dữ liệu xét nghiệm

Vấn đề đơn vị không đồng nhất mà chúng tôi gặp phải đã được biết đến ở quy mô
lớn hơn. Từ 6% đến 19% xét nghiệm không ánh xạ chính xác được sang LOINC, với
đơn vị thiếu hoặc sai nằm trong số các trở ngại lặp lại [14]; một phân tích
trên hơn 163 triệu kết quả đã gắn mã LOINC tìm thấy 2.019 cách viết đơn vị
khác nhau, rút xuống còn khoảng 40 đơn vị chuẩn sau khi hài hòa hóa [15]. Đã
có các hướng tự động hóa cho phần ánh xạ mã [16] và cho phần hài hòa đơn vị
bằng truy hồi kết hợp xếp hạng lại [17].

Tài liệu này coi sự không đồng nhất về đơn vị là trở ngại cho việc tổng hợp dữ
liệu và phân tích thứ cấp. Quan sát của chúng tôi là nó còn là vấn đề an toàn
bệnh nhân theo nghĩa lâm sàng trực tiếp. Trong quy trình của chúng tôi, so
sánh một giá trị chưa quy đổi với khoảng tham chiếu ghi bằng đơn vị khác đã
tạo ra phân loại sai nghiêm trọng cho một kết quả bình thường, và sai ngay
bên trong tầng xác định mà toàn bộ phần còn lại của kiến trúc tin cậy vào.
Lập luận ủng hộ chuẩn hóa thường được nêu dưới góc độ tái sử dụng dữ liệu cho
nghiên cứu; chúng tôi đóng góp một mẩu bằng chứng rằng nó còn ảnh hưởng đến
điều mà bệnh nhân được nghe về kết quả của chính mình.

---

## 3. Thiết kế hệ thống

Nguyên tắc thiết kế trung tâm là không giao bất kỳ phán đoán lâm sàng nào
cho mô hình ngôn ngữ. Việc một chỉ số có bất thường hay không, và bất thường
đến mức nào, do luật xác định trước khi mô hình được gọi. Mô hình nhận các giá
trị đã được gán nhãn và chỉ được yêu cầu diễn đạt lại. Một bộ kiểm chứng sau
sinh sẽ kiểm tra văn bản sinh ra có nhất quán với các nhãn đó không, và thay
bằng bản mẫu cố định khi không nhất quán.

Hình 1 minh họa bốn tầng của quy trình.

### Tầng 1 — Chuẩn hóa tên và đơn vị

Các phòng xét nghiệm Việt Nam gọi tên cùng một chỉ số theo nhiều cách khác
nhau: số lượng bạch cầu có thể xuất hiện là `WBC`, viết tắt tiếng Việt `SLBC`,
cụm tiếng Việt đầy đủ, hoặc `* WBC`. Tỷ lệ phần trăm và số lượng tuyệt đối chỉ
phân biệt bằng ký hiệu `%` hoặc `#`, và ký hiệu này có thể đứng trước hoặc sau
tên chỉ số (`NEUT%` so với `% Neu`). Tầng 1 ánh xạ chúng về mã chuẩn qua một
từ điển bí danh. Cách chuẩn hóa ngây thơ, tức xóa hết dấu câu, sẽ làm `NEUT%`
và `NEUT#` gộp thành một khóa, nên các ký hiệu này được giữ lại thành token
tường minh.

Sai lệch về đơn vị gây hậu quả nặng hơn nhiều so với sai lệch về tên chỉ số.
Cùng chỉ số huyết sắc tố, có phòng xét nghiệm ghi theo `g/L`, có phòng ghi
theo `g/dL`; hai đơn vị này chênh nhau mười lần. Ví dụ cụ thể: một người có
huyết sắc tố 140 `g/L`, tức 14 `g/dL`, là hoàn toàn bình thường. Nếu con số 14
được đem so thẳng với khoảng tham chiếu tính bằng `g/L` (khoảng 130–170) mà
không quy đổi, hệ thống sẽ kết luận người này thiếu máu rất nặng và cần đi
khám gấp. Cảnh báo giả đó sinh ra ngay bên trong tầng luật, tầng mà cả kiến
trúc dựa vào để đảm bảo tính đúng đắn.

Vì vậy Tầng 1 quy đổi mọi giá trị về đơn vị chuẩn, và từ chối xử lý một chỉ
số khi đơn vị không nhận ra được, hoặc khi phiếu thiếu đơn vị mà chỉ số đó
có nhiều đơn vị khác nhau về bậc độ lớn. Các chỉ số bị từ chối được báo cáo
riêng và không tính vào nhãn tổng thể của phiếu. Hệ thống không bao giờ đoán.

### Tầng 2 — Phân loại bằng luật

Mỗi giá trị đã chuẩn hóa được so với khoảng tham chiếu của nó và gán một trong
ba nhãn theo Bảng 1.

**Bảng 1. Ba mức nhãn của Tầng 2 và điều kiện gán nhãn.**

| Nhãn | Điều kiện |
|---|---|
| **Bình thường** | Nằm trong khoảng tham chiếu |
| **Theo dõi** | Ngoài khoảng nhưng trong ngưỡng mức độ cấu hình được |
| **Nên khám sớm** | Vượt quá ngưỡng đó |

Nhãn của cả phiếu là nhãn nghiêm trọng nhất trong các chỉ số.

Tầng này không có thành phần học máy nào. Do đó độ chính xác phân loại là một
thuộc tính của thiết kế chứ không phải kết quả thực nghiệm, và mô hình ngôn
ngữ không có cơ hội nào để thay đổi nó.

Ngưỡng phân biệt theo dõi với nên khám sớm được định nghĩa riêng cho từng chỉ
số theo công thức `ngưỡng = severity_factor × (cao − thấp)`, trong đó cao và
thấp là hai đầu của khoảng tham chiếu, còn `severity_factor` nằm trong khoảng
0,15–0,50 tùy chỉ số (22 chỉ số dùng trong nghiên cứu này). Các hệ số này
được đặt theo kinh nghiệm cho nghiên cứu này, chứ không suy ra từ dữ liệu lâm
sàng thật hay danh mục giá trị nguy kịch của phòng xét nghiệm nào. Phần Hạn
chế (mục 7) bàn thêm về lựa chọn này.

### Tầng 3 — Sinh văn bản có ràng buộc

Prompt đưa cho mô hình chứa, với mỗi chỉ số: giá trị, khoảng tham chiếu, chiều
lệch và mức độ đã được xác định sẵn, cùng mô tả chức năng của chỉ số bằng
ngôn ngữ đời thường. Ba lớp ràng buộc được áp dụng:

- **Ràng buộc đầu vào** — không để lại cơ hội nào cho việc tự đánh giá: mô
  hình được cho nhãn, không được yêu cầu suy ra nhãn.
- **Ràng buộc nội dung** — cấm gọi tên bệnh, cấm quy nguyên nhân, cấm nhắc đến
  thuốc, liều lượng hay cách điều trị.
- **Ràng buộc đầu ra** — bắt buộc theo một schema JSON cố định, nhờ đó mới
  kiểm tra tự động được.

Chúng tôi dùng Qwen2.5-3B chạy tại chỗ qua Ollama. Lựa chọn mô hình là có chủ
đích: dữ liệu xét nghiệm là dữ liệu nhạy cảm, và một hệ thống dành cho bệnh
viện Việt Nam không nên truyền nó ra dịch vụ bên ngoài. Một mô hình đủ nhỏ để
chạy trên phần cứng CPU thông thường loại bỏ cả mối lo về quyền riêng tư lẫn
yêu cầu đầu tư GPU.

### Tầng 4 — Kiểm chứng sau sinh

Bộ kiểm chứng đối chiếu từng mục sinh ra với nhãn của Tầng 2:

- Chiều lệch nêu trong văn bản có khớp chiều đã gán không
- Có xuất hiện từ khóa cấm không
- Mọi chỉ số đầu vào có được nhắc đến không
- Có chỉ số nào không có trong đầu vào bị đưa thêm vào không

Ngoài ra nó kiểm tra câu kết xem có trấn an sai không, tức khẳng định mọi
kết quả đều bình thường trên một phiếu không bình thường.

Đầu ra không qua kiểm chứng sẽ được sinh lại, đến một giới hạn số lần, sau đó
hệ thống phát ra bản mẫu cố định ghi giá trị, khoảng tham chiếu và nhãn đã
gán. Nhờ vậy quy trình không bao giờ trả về văn bản chưa được kiểm chứng.

Trước khi khớp mẫu, văn bản sinh ra được chuẩn hóa bằng cách bỏ dấu tiếng
Việt và chuyển thành chữ thường. Các cụm chỉ khoảng tham chiếu chứ không phải
lời khẳng định trạng thái, ví dụ "cao hơn mức bình thường", được gỡ bỏ khi
chúng đứng sau một từ so sánh, để chữ "bình thường" bên trong không bị hiểu
nhầm thành khẳng định trạng thái.

---

## 4. Phương pháp đánh giá

### 4.1. Dữ liệu

Chúng tôi đánh giá trên 150 phiếu công thức máu tổng hợp thay vì hồ sơ lâm
sàng. Dữ liệu tổng hợp ở đây là bắt buộc chứ không chỉ là tiện lợi:

- Đo tính nhất quán đòi hỏi nhãn đúng biết trước, mà phiếu thật không kèm
  theo.
- Nó cho phép thiết kế cân bằng, các lớp mức độ có số lượng ngang nhau, trong
  khi phiếu thật đa số là bình thường và sẽ cho rất ít ca bất thường để kiểm
  thử.
- Nó tránh hoàn toàn việc xử lý dữ liệu bệnh nhân.

Mỗi phiếu chứa 10–18 chỉ số, chia đều giữa ba lớp bình thường, theo dõi và
khám sớm, sinh ra bằng cách chọn ngẫu nhiên bí danh và đơn vị để Tầng 1 được
kiểm thử thật sự. Việc làm tròn được áp dụng đúng như cách phòng xét nghiệm in
ra, và phiếu nào sau khi làm tròn không còn khớp lớp đích thì bị loại bỏ và
sinh lại.

### 4.2. Ba cấu hình so sánh

Ba cấu hình được so sánh trên cùng bộ dữ liệu, mô tả ở Bảng 2. Mỗi cấu hình
bật thêm một phần của kiến trúc, để thấy từng tầng đóng góp gì.

**Bảng 2. Ba cấu hình thực nghiệm.**

| Cấu hình | Mô tả |
|---|---|
| **baseline** | Đưa thẳng giá trị thô và khoảng tham chiếu cho mô hình, yêu cầu giải thích cho bệnh nhân. Không nhãn, không ràng buộc, không kiểm chứng. Đây xấp xỉ thực tế hiện nay khi bệnh nhân dán phiếu vào chatbot. |
| **constrained** | Tầng 1–3: mô hình nhận nhãn đã gán sẵn dưới ba lớp ràng buộc, nhưng đầu ra không được kiểm chứng. |
| **full** | Tầng 1–4, gồm kiểm chứng, sinh lại và bản mẫu dự phòng. |

### 4.3. Các chỉ số đo

Mọi chỉ số được tính theo từng phiếu bởi bộ kiểm chứng Tầng 4.

- **Đầu ra an toàn** — tỷ lệ phiếu có đầu ra cuối cùng qua được kiểm chứng,
  tính cả phiếu dùng bản mẫu dự phòng.
- **Mô hình tự đạt** — chỉ tính phiếu mà chính mô hình sinh ra được nội dung
  đạt yêu cầu.
- Các chỉ số còn lại đếm số phiếu có ít nhất một trường hợp: trấn an sai, sai
  chiều lệch, câu chữ mâu thuẫn, dùng thuật ngữ bị cấm, bịa chỉ số, bỏ sót
  chỉ số.

**Sai chiều lệch** và **câu chữ mâu thuẫn** là hai phép kiểm khác nhau. Cái
thứ nhất đối chiếu trường trạng thái có cấu trúc với nhãn của Tầng 2; cái thứ
hai quét phần văn xuôi xem có câu nào khẳng định một trạng thái khác không.
Mô hình hoàn toàn có thể điền đúng trường trạng thái nhưng lại mô tả sai trong
lời văn, và chỉ phép kiểm thứ hai bắt được. Cả sáu loại lỗi đều tham gia quyết
định một đầu ra có qua kiểm chứng hay không.

---

## 5. Kết quả

**Bảng 3. So sánh ba cấu hình trên 150 phiếu tổng hợp (%). Cột lỗi càng thấp
càng tốt.**

| Cấu hình | Đầu ra an toàn | Mô hình tự đạt | Trấn an sai | Sai chiều lệch | Mâu thuẫn | Từ cấm | Bịa chỉ số | Bỏ sót |
|---|---|---|---|---|---|---|---|---|
| **baseline** | 0,0 | 0,0 | 32,0 | 91,3 | 56,0 | 79,3 | 32,0 | 71,3 |
| **constrained** | 48,0 | 48,0 | 8,0 | 12,7 | 5,3 | 15,3 | 10,0 | 28,7 |
| **full** | **100,0** | 64,0 | **0,0** | **0,0** | **0,0** | **0,0** | **0,0** | **0,0** |

Bảng 3 cho thấy một quy luật nhất quán: mọi chỉ số lỗi đều giảm đơn điệu khi
đi từ `baseline` sang `constrained` rồi sang `full`, không có chỉ số nào tăng
trở lại ở bước sau. Điều này có nghĩa hai cơ chế được thêm vào không xung đột
nhau: ràng buộc prompt (bước từ `baseline` sang `constrained`) cắt phần lớn
lỗi, còn kiểm chứng bằng máy (bước từ `constrained` sang `full`) dọn nốt phần
còn lại.

Mức độ đóng góp của hai cơ chế rất khác nhau. Ràng buộc prompt tạo ra bước
nhảy lớn nhất về mặt số lượng: sai chiều lệch giảm từ 91,3% xuống 12,7%, từ
cấm từ 79,3% xuống 15,3%, câu chữ mâu thuẫn từ 56,0% xuống 5,3%. Nhưng nó
không đưa được chỉ số nào về 0, và tỷ lệ đầu ra an toàn chỉ đạt 48,0%, tức
hơn một nửa số phiếu vẫn không dùng được. Kiểm chứng bằng máy mới là bước đưa
toàn bộ sáu loại lỗi về 0 và đưa tỷ lệ an toàn lên 100%.

Cần đọc con số 100% này cho đúng: nó là tỷ lệ đầu ra **cuối cùng** đạt yêu
cầu, trong đó 64,0% do mô hình tự viết được và 36,0% còn lại là bản mẫu cố
định thay thế sau khi sinh lại vẫn không đạt. Nói cách khác, đây là tính chất
của quy trình, không phải bằng chứng rằng mô hình 3B viết đúng trong mọi
trường hợp.

### Sinh văn bản không ràng buộc là không an toàn

Cấu hình baseline không tạo ra đầu ra đạt yêu cầu nào trên cả 150 phiếu. Nó
nói sai chiều lệch của ít nhất một chỉ số ở 91,3% số phiếu, và dùng thuật ngữ
lâm sàng bị cấm ở 79,3%. Trên các phiếu có kết quả bất thường, nó khẳng định
mọi kết quả đều bình thường ở 32,0% số ca. Nghĩa là cứ khoảng ba bệnh nhân thì
một người bị nói sai rằng không có gì cần quan tâm.

### Ràng buộc bằng prompt có tác dụng nhưng chưa đủ

Cung cấp nhãn có sẵn giúp giảm sai chiều lệch từ 91,3% xuống 12,7% và trấn an
sai từ 32,0% xuống 8,0%. Tuy vậy 52,0% đầu ra của constrained vẫn không qua
kiểm chứng. Dặn dò không đảm bảo tuân thủ, đó là lý do cần một bước kiểm
chứng bằng máy.

### Kiểm chứng loại bỏ hoàn toàn đầu ra không an toàn

Cấu hình full qua kiểm chứng trên cả 150 phiếu. Con số này cần được nói rõ:
64,0% số phiếu do mô hình sinh ra, còn 36,0% rơi về bản mẫu cố định sau khi
sinh lại thất bại. Đảm bảo an toàn là thuộc tính của quy trình, không phải
bằng chứng rằng mô hình 3B làm được việc này một cách đáng tin cậy.

Tỷ lệ mô hình tự đạt ở full là 64,0%, cao hơn 48,0% của constrained, cho thấy
cơ chế sinh lại cứu được một phần đáng kể những đầu ra thất bại ở lần đầu.

### Định dạng và chi phí

Ở baseline, 97,3% đầu ra gọi tên chỉ số bằng tên hiển thị thay vì mã chuẩn, và
2,0% không phân tích cú pháp được; cả hai đều về 0 khi áp ràng buộc schema.
Chúng tôi đếm riêng những lỗi này khỏi lỗi nội dung, vì phạt một cấu hình về
định dạng mà nó chưa từng được yêu cầu tuân theo sẽ thổi phồng số lỗi nội
dung của nó.

Thời gian xử lý trung bình là 38,9 giây ở baseline, 35,8 giây ở constrained,
và 68,3 giây ở full, với trung bình 1,97 lần sinh ở cấu hình cuối. An toàn
phải trả giá khoảng gấp đôi về độ trễ. Mọi phép đo thực hiện trên Intel Core
i5-9400F, 24 GB RAM, không dùng GPU.

---

## 6. Thảo luận

### 6.1. Giao cho mỗi thành phần việc mà nó làm tốt

Kết quả ủng hộ một sự phân công lao động, chứ không phải một cải tiến về
cách viết prompt. Cấu hình baseline yêu cầu mô hình làm hai việc cùng lúc:
phán đoán từng giá trị và giải thích chúng. Nó thất bại ở việc thứ nhất trên
91,3% số phiếu trong khi vẫn viết văn trôi chảy suốt. Khi chuyển phán đoán
sang tầng luật, phân loại trở nên chính xác theo cấu trúc, và mô hình chỉ còn
việc diễn đạt lại, việc nó làm ở mức chấp nhận được.

Một hệ quả hữu ích là hai thành phần cải thiện độc lập với nhau. Thay các
ngưỡng mức độ kinh nghiệm bằng danh mục giá trị nguy hiểm (critical value) của
một phòng xét nghiệm sẽ đổi các nhãn mà mô hình nhận, nhưng không đổi gì khác
trong kiến trúc, và Bảng 1 vẫn giữ nguyên giá trị, vì nó đo sự khớp nhau giữa
văn bản sinh ra và nhãn được gán, chứ không đo mức tối ưu lâm sàng của các
nhãn ấy. Tương tự, một mô hình lớn hơn sẽ nâng tỷ lệ mô hình tự đạt mà không
thay đổi đảm bảo an toàn, vì đảm bảo đó do Tầng 4 cung cấp.

### 6.2. Trấn an sai xứng đáng là một chỉ số riêng

Các đánh giá về diễn giải cho bệnh nhân thường báo cáo độ dễ đọc và độ chính
xác. Không chỉ số nào trong hai chỉ số đó bắt được lỗi mà chúng tôi cho là tai
hại nhất. Một câu nói rằng mọi kết quả đều bình thường, đặt trên một phiếu
không bình thường, chỉ là một câu giữa nhiều câu, và thậm chí có thể được
chấm điểm dễ đọc cao chính vì nó đơn giản và trấn an. Tác hại của nó nằm ở
việc nó khiến người đọc không làm gì.

Dữ liệu của chúng tôi cho thấy lỗi này không hiếm và không bị loại bỏ bằng
việc dặn dò: 32,0% ở baseline, và sau khi đã có ràng buộc prompt cấm rõ ràng,
vẫn còn 8,0% ở constrained; chỉ về 0 khi có kiểm chứng bằng máy. Mọi hệ thống
sinh diễn giải kết quả xét nghiệm cho bệnh nhân nên báo cáo chỉ số này, và
một lệnh cấm ở mức prompt không nên được chấp nhận như bằng chứng rằng lỗi đã
không còn.

### 6.3. Đơn vị không đồng nhất là vấn đề an toàn, không phải vấn đề định dạng

Thất bại đáng học hỏi nhất gặp trong quá trình phát triển lại xảy ra ở chính
tầng mà kiến trúc coi là đáng tin cậy. Tầng 2 là xác định, và phân loại của
nó chính xác tuyệt đối, nhưng chỉ đối với những con số nó nhận được. Khi nhận
huyết sắc tố đo bằng `g/dL` rồi so với khoảng tham chiếu `g/L`, nó xếp một giá
trị bình thường thành cần khám khẩn, và làm vậy với sự nhất quán nội tại hoàn
hảo. Không có mức kiểm chứng nào ở phía sau phát hiện được điều này, vì mọi
tầng tiếp theo sẽ trung thành tái tạo một nhãn sai một cách tự tin.

Điều này chuyển chuẩn hóa dữ liệu từ chỗ là tiện lợi về khả năng liên thông
thành điều kiện tiên quyết về an toàn. Mọi tuyên bố về tính đúng đắn của một
tầng lâm sàng dựa trên luật đều có điều kiện là dữ liệu đã ở đơn vị chuẩn, và
bước quy đổi phải biết từ chối thay vì đoán. Các hệ mã như LOINC và chuẩn
trao đổi như HL7 FHIR giải quyết đúng vấn đề này. Quan sát ở đây là một mẩu
bằng chứng thực nghiệm ủng hộ việc áp dụng chúng trong báo cáo xét nghiệm ở
Việt Nam.

### 6.4. Cân nhắc khi triển khai

Chạy mô hình 3B trên CPU là chậm, 68,3 giây mỗi phiếu ở quy trình đầy đủ,
nhưng chấp nhận được với một tác vụ thực hiện một lần cho mỗi phiếu chứ không
phải tương tác liên tục. Đổi lại, nó mang đến hai tính chất quan trọng: dữ
liệu bệnh nhân không rời khỏi cơ sở y tế, và không cần GPU, nên rào cản phần
cứng với một bệnh viện tuyến tỉnh chỉ là chiếc máy họ đã có.

Tỷ lệ 36,0% dùng bản mẫu dự phòng là cái giá của mô hình nhỏ. Với phần phiếu
đó, hệ thống suy giảm về mức không tốt hơn phiếu gốc, nhưng cũng không tệ hơn
và không bao giờ gây hiểu lầm.

---

## 7. Giới hạn của nghiên cứu

**Chưa có thẩm định lâm sàng.** Toàn bộ đánh giá là tự động. Không có chuyên
gia y tế nào rà soát các lời giải thích sinh ra, nên chúng tôi chỉ có thể
khẳng định đầu ra nhất quán nội tại với các nhãn đã gán, chứ không khẳng định
chúng phù hợp về mặt lâm sàng hay thực sự dễ hiểu với bệnh nhân.

**Ngưỡng mức độ chưa có căn cứ lâm sàng.** Các hệ số phân biệt theo dõi với
nên khám sớm được đặt theo kinh nghiệm để minh họa kiến trúc, chưa được đối
chiếu với danh mục giá trị nguy hiểm của bất kỳ phòng xét nghiệm nào, và
không nên được hiểu là khuyến nghị lâm sàng.

**Dữ liệu tổng hợp và kiểm chứng dựa trên khớp mẫu.** Phiếu là sinh ra chứ
không phải lâm sàng; phiếu thật có nhiễu, thiếu trường và biến thể định dạng
mà nghiên cứu này chưa bao quát. Tầng 4 khớp mẫu bề mặt nên có thể bị lách
bằng cách diễn đạt vòng vo. Nó chặn được những lỗi mà nó được thiết kế để
phát hiện, không phải mọi nội dung không an toàn.

**Phạm vi.** Chỉ hỗ trợ công thức máu; chưa xử lý sinh hóa, miễn dịch, khoảng
tham chiếu một phía và kết quả định tính, và khoảng tham chiếu chưa phân theo
giới tính hay độ tuổi. Giả định đầu vào đã có cấu trúc nên OCR nằm ngoài phạm
vi. Kết quả chỉ từ một mô hình 3B duy nhất.

---

## 8. Kết luận

Chúng tôi trình bày một quy trình giải thích kết quả xét nghiệm máu cho bệnh
nhân, trong đó mô hình ngôn ngữ không được phép phán đoán một giá trị có bất
thường hay không. Luật xác định điều đó trước; mô hình diễn đạt lại kết quả;
một bộ kiểm chứng đối chiếu bản diễn đạt với kết luận đó và thay bằng bản mẫu
cố định khi hai bên không khớp.

Trên 150 phiếu tổng hợp, trấn an sai giảm từ 32,0% khi không ràng buộc xuống
8,0% khi có ràng buộc prompt, rồi xuống 0 khi có kiểm chứng, và quy trình đầy
đủ không tạo ra đầu ra không an toàn nào. Hệ thống chạy trên CPU không cần
GPU, giữ dữ liệu xét nghiệm bên trong cơ sở y tế.

---

## 9. Hướng phát triển

Năm hướng phát triển tiếp theo, xếp theo thứ tự ưu tiên:

1. **Thẩm định lâm sàng** là cấp thiết nhất. Đánh giá hiện tại thiết lập tính
   nhất quán nội tại, không phải sự phù hợp lâm sàng; cần chuyên gia rà soát
   trước khi có thể tuyên bố bất cứ điều gì về lợi ích cho bệnh nhân.
2. **Thay ngưỡng kinh nghiệm** bằng danh mục giá trị nguy hiểm đã được thiết
   lập.
3. **Mở rộng phạm vi** ra ngoài công thức máu, sang các nhóm xét nghiệm có
   khoảng tham chiếu một phía và kết quả định tính.
4. **Thêm tầng giọng nói** phục vụ người cao tuổi và người đọc kém, vì tầng
   này chỉ tiêu thụ văn bản đã kiểm chứng nên không thể tạo ra lỗi nội dung
   mới.
5. **Đánh giá trên phiếu thật** từ nhiều phòng xét nghiệm, để kiểm thử phần
   chuẩn hóa tên và đơn vị trước mức độ biến thiên mà nghiên cứu này mới chỉ
   mô phỏng gần đúng.

---

## Phụ lục: Đối chiếu thuật ngữ Việt – Anh

Bảng 4 đối chiếu các thuật ngữ dùng trong bản tiếng Việt với thuật ngữ tương
ứng ở bản tiếng Anh nộp hội nghị.

**Bảng 4. Đối chiếu thuật ngữ Việt – Anh.**

| Tiếng Việt | Tiếng Anh trong bài |
|---|---|
| Năng lực hiểu biết sức khỏe | health literacy |
| Trấn an sai | false reassurance |
| Sai chiều lệch | direction mismatch |
| Câu chữ mâu thuẫn | contradictory wording |
| Bịa chỉ số | fabricated analyte |
| Bỏ sót chỉ số | omitted analyte |
| Từ khóa bị cấm | forbidden terms |
| Đầu ra an toàn | safe output |
| Mô hình tự đạt | model-generated pass |
| Bản mẫu dự phòng / đường lui | fallback template |
| Khoảng tham chiếu | reference interval |
| Giá trị nguy hiểm | critical value |
| Ràng buộc theo luật | rule-constrained |
| Kiểm chứng sau sinh | post-generation validation |
| Dữ liệu tổng hợp | synthetic data |
| Chỉ số (xét nghiệm) | analyte |
| Phiếu xét nghiệm | panel |
