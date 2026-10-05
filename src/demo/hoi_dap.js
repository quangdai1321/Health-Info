/* Hoi dap sau khi co ket qua.
   Van giu nguyen tac cua bai bao: mo hinh khong duoc tu phan doan.
   - Chi duoc tra loi dua tren bang du kien da tinh o tang 1 va 2.
   - Cam chan doan, cam quy nguyen nhan, cam thuoc va dieu tri.
   - Cau tra loi van phai qua kiem tra, khong dat thi thay bang cau mau. */

const CAU_CHOI = "Chỗ này tôi không trả lời được, vì hệ thống chỉ giải thích những con số in trên " +
  "phiếu, không chẩn đoán bệnh và không tư vấn điều trị. Bạn nên hỏi bác sĩ.";

/* Bang du kien: tat ca nhung gi mo hinh duoc phep dua vao */
function bangDuKien(kq) {
  const dong = kq.ket.map((k) =>
    `- ${k.ten} (${k.code}): ${k.goc} | khoảng tham chiếu ${k.thap}–${k.cao} ${k.dv} | ` +
    `kết luận: ${k.chieu === "trong_khoang" ? "trong khoảng" : k.chieu === "cao" ? "cao hơn khoảng" : "thấp hơn khoảng"} | ` +
    `mức: ${TEN_MUC[k.muc]} | chỉ số này ${k.congdung}`);
  return dong.join("\n") + `\n\nMức chung của cả phiếu: ${TEN_MUC[kq.nhanPhieu]}.`;
}

function promptHoiDap(kq, cauHoi, lichSu) {
  const truoc = lichSu.slice(-4).map((x) => `${x.ai === "nguoi" ? "Người bệnh" : "Bạn"}: ${x.chu}`).join("\n");
  return `Bạn giúp người bệnh hiểu phiếu xét nghiệm của họ.

CHỈ ĐƯỢC dùng bảng dữ kiện dưới đây. Không được thêm con số nào khác, không được suy đoán.

QUY TẮC BẮT BUỘC:
1. Cấm nêu tên bệnh, cấm đoán nguyên nhân, cấm nhắc thuốc, liều lượng hay cách điều trị.
2. Không được nói phiếu bình thường nếu mức chung khác "Bình thường".
3. Câu hỏi nằm ngoài bảng dữ kiện thì trả lời đúng câu này: "${CAU_CHOI}"
4. Trả lời ngắn, tối đa ba câu, bằng từ ngữ thông thường.
5. Trả về đúng JSON: {"answer":"..."} và không thêm gì ngoài JSON.

BẢNG DỮ KIỆN:
${bangDuKien(kq)}
${truoc ? "\nTRAO ĐỔI TRƯỚC ĐÓ:\n" + truoc : ""}

CÂU HỎI: ${cauHoi}`;
}

/* Kiem tra cau tra loi, dung lai cac phep thu cua tang 4 */
function kiemTraTraLoi(chuTraLoi, kq) {
  const loi = [];
  const chu = chuan(chuTraLoi);
  const sach = CUM_THAM_CHIEU.reduce((t, re) => t.replace(re, " THAM_CHIEU "), chu);

  for (const re of TU_CAM) {
    const m = chu.match(re);
    if (m) { loi.push({ loai: "dùng từ bị cấm", chi_tiet: m[0] }); break; }
  }
  if (kq.nhanPhieu !== MUC.BT && TU_TRAN_AN.some((re) => re.test(chu)))
    loi.push({ loai: "trấn an sai", chi_tiet: "nói mọi thứ bình thường trên phiếu bất thường" });

  // noi nguoc ket luan cua tang 2, xet tung chi so duoc nhac ten trong cau tra loi.
  // Dò ca ten day du lan ten goi tat, vi nguoi benh hay noi "bach cau" thay vi "so luong bach cau".
  for (const k of kq.ket) {
    const ten = [chuan(k.ten), chuan(k.code)];
    for (const [alias, ma] of DS_ALIAS) if (ma === k.code && alias.length >= 3) ten.push(alias);
    const viTri = Math.max(...ten.map((t) => sach.indexOf(t)));
    if (viTri < 0) continue;
    const doan = sach.slice(viTri, viTri + 170);
    for (const [tt, mau] of Object.entries(TU_TRANG_THAI)) {
      if (tt !== k.chieu && mau.some((re) => re.test(doan))) {
        loi.push({ loai: "nói ngược kết luận", chi_tiet: `${k.code}: nói "${tt}" nhưng thực tế "${k.chieu}"` });
        break;
      }
    }
  }

  // con so la: moi con so trong cau tra loi deu phai co trong bang du kien
  const choPhep = new Set();
  kq.ket.forEach((k) => [k.gt, k.thap, k.cao].forEach((v) => {
    choPhep.add(String(v));
    choPhep.add(String(v).replace(".", ","));
    choPhep.add(String(Math.round(v * 100) / 100));
  }));
  for (const so of chuTraLoi.match(/\d+[.,]?\d*/g) || []) {
    if (so.length <= 1) continue;                       // bo qua so dem nho
    if (!choPhep.has(so) && !choPhep.has(so.replace(",", "."))) {
      loi.push({ loai: "con số không có trong phiếu", chi_tiet: so });
      break;
    }
  }
  return { dat: loi.length === 0, loi };
}

/* Tra loi mot cau hoi. Khong dat thi sinh lai, van khong dat thi dung cau choi. */
async function traLoiCauHoi(cauHoi, kq, url, model, lichSu, soLan = 2, log) {
  const prompt = promptHoiDap(kq, cauHoi, lichSu || []);
  let cuoi = null;
  for (let lan = 1; lan <= soLan; lan++) {
    let chu = "";
    try {
      const r = await goiOllama(url, model, prompt, true);
      chu = String(JSON.parse(r.text).answer || "").trim();
    } catch (e) {
      cuoi = { lan, kt: { dat: false, loi: [{ loai: "không đọc được trả lời", chi_tiet: String(e.message || e) }] } };
      log && log(cuoi);
      continue;
    }
    if (!chu) { cuoi = { lan, kt: { dat: false, loi: [{ loai: "trả lời rỗng", chi_tiet: "" }] } }; log && log(cuoi); continue; }
    if (chu === CAU_CHOI) return { chu, kt: { dat: true, loi: [] }, lan, tuChoi: true };
    const kt = kiemTraTraLoi(chu, kq);
    cuoi = { lan, chu, kt };
    log && log(cuoi);
    if (kt.dat) return { chu, kt, lan, tuChoi: false };
  }
  return { chu: CAU_CHOI, kt: { dat: true, loi: [] }, lan: soLan, dungCauMau: true, truot: cuoi };
}
