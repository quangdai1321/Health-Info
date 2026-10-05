/* Doc ket qua thanh tieng.
   Hai duong:
   1. Giong trinh duyet (Web Speech API): mien phi, khong gui chu di dau.
   2. Gemini Live API: giong nguoi Viet that, nhanh, nhung chu duoc gui len may chu Google
      va can khoa API. Dung WebSocket nen khong vuong CORS. */

const WS_GEMINI = "wss://generativelanguage.googleapis.com/ws/" +
  "google.ai.generativelanguage.v1beta.GenerativeService.BidiGenerateContent";
const MODEL_LIVE = "models/gemini-3.8-live";
const DAN_DOC = "Bạn chỉ đọc lại nguyên văn đoạn văn người dùng gửi, bằng tiếng Việt. " +
  "Không chào hỏi, không bình luận, không tóm tắt, không thêm bớt chữ nào.";

let dangDoc = null;          // doi tuong Audio dang phat
let dangNoi = null;          // ket noi WebSocket dang mo
let luotDoc = 0;             // bam doc lan thu may, de bo qua ket qua cu

function dungDoc() {
  luotDoc++;
  try { window.speechSynthesis.cancel(); } catch (e) {}
  if (dangDoc) { dangDoc.pause(); dangDoc = null; }
  if (dangNoi) { try { dangNoi.close(); } catch (e) {} dangNoi = null; }
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

/* Toc do doc. 1,0 la toc do goc cua may, cac giong Gemini o muc nay noi cham hon nguoi that. */
let tocDo = 1.35;
function datTocDo(v) { tocDo = Math.min(2, Math.max(0.6, Number(v) || 1.35)); }

function docBangTrinhDuyet(chu, xong) {
  if (!window.speechSynthesis) throw new Error("trình duyệt này không có sẵn giọng đọc");
  dungDoc();
  const u = new SpeechSynthesisUtterance(chu);
  const v = timGiongViet();
  if (v) { u.voice = v; u.lang = v.lang; } else { u.lang = "vi-VN"; }
  u.rate = Math.min(2, tocDo * 0.95);
  u.onend = () => xong && xong(v ? v.name : "giọng mặc định");
  u.onerror = (e) => xong && xong(null, e.error || "lỗi khi đọc");
  window.speechSynthesis.speak(u);
  return v;
}

// ---------------------------------------------------------------- Gemini Live
/* Ghep cac manh PCM 16 bit 24 kHz thanh mot file WAV phat duoc */
function ghepWav(manh, tanSo = 24000) {
  const tong = manh.reduce((s, x) => s + x.length, 0);
  const buf = new ArrayBuffer(44 + tong);
  const dv = new DataView(buf);
  const chu = (vt, s) => [...s].forEach((c, i) => dv.setUint8(vt + i, c.charCodeAt(0)));
  chu(0, "RIFF"); dv.setUint32(4, 36 + tong, true); chu(8, "WAVEfmt ");
  dv.setUint32(16, 16, true); dv.setUint16(20, 1, true); dv.setUint16(22, 1, true);
  dv.setUint32(24, tanSo, true); dv.setUint32(28, tanSo * 2, true);
  dv.setUint16(32, 2, true); dv.setUint16(34, 16, true);
  chu(36, "data"); dv.setUint32(40, tong, true);
  const ra = new Uint8Array(buf);
  let vt = 44;
  for (const m of manh) { ra.set(m, vt); vt += m.length; }
  return new Blob([buf], { type: "audio/wav" });
}

const giaiMaB64 = (s) => Uint8Array.from(atob(s), (c) => c.charCodeAt(0));

function docBangGeminiLive(chu, khoa, giong, bao) {
  return new Promise((xong, hong) => {
    dungDoc();
    const luot = luotDoc;                    // dau moc cua lan bam nay
    const ws = new WebSocket(`${WS_GEMINI}?key=${encodeURIComponent(khoa)}`);
    dangNoi = ws;
    const manh = [];
    let loi = null;

    const hetGio = setTimeout(() => { loi = loi || new Error("quá lâu không thấy phản hồi"); ws.close(); }, 60000);

    ws.onopen = () => ws.send(JSON.stringify({
      setup: {
        model: MODEL_LIVE,
        generationConfig: {
          responseModalities: ["AUDIO"],
          speechConfig: {
            voiceConfig: { prebuiltVoiceConfig: { voiceName: giong || "vi-vn-csagent-4" } },
            languageCode: "vi-VN",
          },
        },
        systemInstruction: { parts: [{ text: DAN_DOC }] },
      },
    }));

    ws.onmessage = async (ev) => {
      let m;
      try {
        m = JSON.parse(typeof ev.data === "string" ? ev.data : await ev.data.text());
      } catch (e) { return; }
      if (m.setupComplete) {
        bao && bao("đang tạo giọng đọc…");
        ws.send(JSON.stringify({
          clientContent: { turns: [{ role: "user", parts: [{ text: chu }] }], turnComplete: true },
        }));
        return;
      }
      for (const p of m.serverContent?.modelTurn?.parts || [])
        if (p.inlineData?.data) manh.push(giaiMaB64(p.inlineData.data));
      if (m.serverContent?.turnComplete || m.serverContent?.generationComplete) ws.close();
    };

    ws.onerror = () => { loi = loi || new Error("không kết nối được tới Gemini, kiểm tra khóa API và mạng"); };

    ws.onclose = () => {
      clearTimeout(hetGio);
      dangNoi = null;
      // nguoi dung da bam doc lan khac trong luc cho, bo ket qua cu di
      if (luot !== luotDoc) return xong({ giay: 0, boQua: true });
      if (!manh.length) return hong(loi || new Error("Gemini không trả về âm thanh"));
      const au = new Audio(URL.createObjectURL(ghepWav(manh)));
      au.preservesPitch = true;          // tang toc nhung giu nguyen cao do giong
      au.mozPreservesPitch = true;
      au.webkitPreservesPitch = true;
      au.playbackRate = tocDo;
      dangDoc = au;
      au.play().then(() => xong({ giay: manh.reduce((s, x) => s + x.length, 0) / 48000 / tocDo })).catch(hong);
    };
  });
}
