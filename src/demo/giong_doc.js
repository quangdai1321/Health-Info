/* Doc ket qua thanh tieng.
   Hai duong:
   1. Giong trinh duyet (Web Speech API): mien phi, khong gui chu di dau.
   2. Giong Gemini: hay hon, nhung chu duoc gui len may chu Google va can khoa API. */

const GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/interactions";
const GEMINI_MODEL = "gemini-3.8-flash-tts";

let dangDoc = null;          // doi tuong Audio dang phat, de dung lai

function dungDoc() {
  try { window.speechSynthesis.cancel(); } catch (e) {}
  if (dangDoc) { dangDoc.pause(); dangDoc = null; }
}

/* Gom ket qua bon tang thanh doan van de doc */
function chuDeDoc(ketQua) {
  const ketCau = (t) => (/[.!?]$/.test(t) ? t : t + ".");
  const cau = ketQua.out.items.map((it) => {
    const k = ketQua.kq.ket.find((x) => x.code === it.code);
    let t = (it.explanation || "").replace(/\s+/g, " ").trim();
    // tranh doc lap ten chi so khi cau giai thich da bat dau bang chinh ten do
    if (k && !t.toLowerCase().startsWith(k.ten.toLowerCase())) t = k.ten + ": " + t;
    return ketCau(t);
  });
  if (ketQua.out.closing) cau.push(ketCau(ketQua.out.closing.trim()));
  return cau.join(" ").replace(/\s*\.\s*\./g, ".");
}

// ---------------------------------------------------------------- giong trinh duyet
function timGiongViet() {
  const ds = window.speechSynthesis ? window.speechSynthesis.getVoices() : [];
  return ds.find((v) => /^vi(-|_)?/i.test(v.lang))
      || ds.find((v) => /viet/i.test(v.name))
      || null;
}

function docBangTrinhDuyet(chu, xong) {
  if (!window.speechSynthesis) throw new Error("trình duyệt này không có sẵn giọng đọc");
  dungDoc();
  const u = new SpeechSynthesisUtterance(chu);
  const v = timGiongViet();
  if (v) { u.voice = v; u.lang = v.lang; } else { u.lang = "vi-VN"; }
  u.rate = 0.95;
  u.onend = () => xong && xong(v ? v.name : "giọng mặc định");
  u.onerror = (e) => xong && xong(null, e.error || "lỗi khi đọc");
  window.speechSynthesis.speak(u);
  return v;
}

// ---------------------------------------------------------------- giong Gemini
async function docBangGemini(chu, khoa, giong) {
  // dat khoa o header, khong de trong duong dan, de khoa khong lot vao nhat ky may chu
  const r = await fetch(GEMINI_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-goog-api-key": khoa },
    body: JSON.stringify({
      model: GEMINI_MODEL,
      input: [{ type: "text", text: "Đọc rõ ràng, giọng bình tĩnh: " + chu }],
      response_format: { type: "audio", mime_type: "audio/wav" },
      generation_config: { speech_config: [{ voice: giong || "Kore" }] },
    }),
  });
  if (!r.ok) {
    let chiTiet = "";
    try { chiTiet = (await r.json()).error?.message || ""; } catch (e) {}
    throw new Error(`Gemini trả về lỗi ${r.status}. ${chiTiet}`);
  }
  const d = await r.json();

  // tim phan du lieu am thanh trong cau tra loi, chap nhan vai kieu bo cuc khac nhau
  let b64 = null;
  const dao = (x) => {
    if (b64 || !x || typeof x !== "object") return;
    if (typeof x.data === "string" && x.data.length > 500) { b64 = x.data; return; }
    if (x.inlineData && typeof x.inlineData.data === "string") { b64 = x.inlineData.data; return; }
    Object.values(x).forEach(dao);
  };
  dao(d);
  if (!b64) throw new Error("không tìm thấy dữ liệu âm thanh trong phản hồi của Gemini");

  dungDoc();
  const au = new Audio("data:audio/wav;base64," + b64);
  dangDoc = au;
  await au.play();
  return au;
}
