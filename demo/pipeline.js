/* Bon tang xu ly, viet lai bang JavaScript tu src/classifier.py va src/prompt_builder.py.
   Tang 1, 2, 4 chay ngay trong trinh duyet. Chi tang 3 goi mo hinh qua Ollama. */

// ---------------------------------------------------------------- tien ich
const boDau = (s) =>
  s.normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/đ/g, "d").replace(/Đ/g, "D");

const chuan = (s) => boDau(String(s || "").toLowerCase()).replace(/\s+/g, " ").trim();

// ---------------------------------------------------------------- TANG 1
// Ten chi so, giu lai dau % va # vi chung phan biet "ty le" voi "so luong".
const BANG_TEN = (() => {
  const m = new Map();
  for (const a of CHI_SO) {
    const them = (t) => {
      const k = chuan(t).replace(/\s*\*\s*/g, "");
      if (k) m.set(k, a.code);
    };
    them(a.code);
    them(a.ten);
    a.alias.forEach(them);
    if (a.code.endsWith("_PCT")) {
      them(a.code.replace("_PCT", "%"));
      them("% " + a.code.replace("_PCT", ""));
    }
    if (a.code.endsWith("_ABS")) them(a.code.replace("_ABS", "#"));
  }
  return m;
})();

const timChiSo = (ten) => {
  const k = chuan(ten).replace(/\s*\*\s*/g, "");
  if (BANG_TEN.has(k)) return BANG_TEN.get(k);
  for (const [key, code] of BANG_TEN) if (key === k.replace(/\s/g, "")) return code;
  return null;
};

/* Doc tung dong cua phieu: "WBC 11.8 G/L" hoac "WBC: 11,8 G/L" */
function tang1(vanBan) {
  const nhan = [], tuChoi = [];
  for (const dongGoc of vanBan.split("\n")) {
    const dong = dongGoc.trim();
    if (!dong) continue;
    const m = dong.match(/^(.+?)[\s:=]+(-?\d+[.,]?\d*)\s*([^\s]*)\s*$/);
    if (!m) { tuChoi.push({ dong, ly_do: "không đọc được dòng này" }); continue; }
    const [, tenRaw, soRaw, dvRaw] = m;
    const code = timChiSo(tenRaw);
    if (!code) { tuChoi.push({ dong, ly_do: "không nhận ra tên chỉ số" }); continue; }
    const a = CHI_SO.find((x) => x.code === code);
    const gt = parseFloat(soRaw.replace(",", "."));
    const dv = dvRaw.trim();
    const nhieuDonVi = Object.keys(a.quydoi).length > 1;

    if (!dv) {
      if (nhieuDonVi) { tuChoi.push({ dong, ly_do: "thiếu đơn vị, mà chỉ số này có nhiều đơn vị khác bậc" }); continue; }
      nhan.push({ code, ten: a.ten, gt, dv: a.dv, goc: `${gt}` });
      continue;
    }
    const khoa = Object.keys(a.quydoi).find((u) => chuan(u) === chuan(dv));
    if (!khoa) { tuChoi.push({ dong, ly_do: `đơn vị lạ "${dv}", hệ thống từ chối thay vì đoán` }); continue; }
    nhan.push({ code, ten: a.ten, gt: gt * a.quydoi[khoa], dv: a.dv, goc: `${gt} ${dv}` });
  }
  return { nhan, tuChoi };
}

/* Doc van ban OCR tu anh chup phieu, lay ra cac dong "MA gia-tri don-vi".
   Dong tren phieu that thuong co ca khoang tham chieu o cuoi, vi du
   "Bach cau (WBC)  11.8  10^9/L  4.0 - 10.0", nen chi lay SO DAU TIEN sau ten. */
const DS_ALIAS = (() => {
  const ds = [];
  for (const a of CHI_SO) {
    const them = (t) => { const k = chuan(t).replace(/\s*\*\s*/g, ""); if (k.length >= 2) ds.push([k, a.code]); };
    them(a.code);
    them(a.ten);
    a.alias.forEach(them);
  }
  return ds.sort((x, y) => y[0].length - x[0].length);     // uu tien ten dai, tranh khop nham
})();

const DS_DON_VI = (() => {
  const s = new Set(["%"]);
  CHI_SO.forEach((a) => Object.keys(a.quydoi).forEach((u) => s.add(u)));
  return [...s];
})();

/* May doc anh hay nham: GIL thay cho G/L, TIL thay cho T/L, mui ten dinh vao con so */
const SUA_DON_VI = {
  gil: "G/L", g1l: "G/L", "g/l": "G/L", gl: "g/L", gdl: "g/dL", "g/dl": "g/dL",
  til: "T/L", t1l: "T/L", "t/l": "T/L", ml: "T/L", "10^9/l": "10^9/L", "10*9/l": "10^9/L",
  "109/l": "10^9/L", "1012/l": "10^12/L", "10^12/l": "10^12/L", fl: "fL", il: "fL",
  pg: "pg", "k/ul": "K/uL", kul: "K/uL", "%": "%",
};

/* Bo mui ten, dau ngoac, gach dung ma may doc anh hay chen vao */
const donRac = (t) => t.replace(/[↑↓|\]\[}{)(*]/g, " ").replace(/\s+/g, " ").trim();

/* Lay so dau tien hop le trong mot chuoi, bo ky tu la bam vao hai dau */
function laySo(tok) {
  const m = tok.replace(",", ".").match(/\d+(?:\.\d+)?/);
  return m ? m[0] : null;
}

function docAnhSangPhieu(vanBanOCR) {
  const dong = [], boQua = [], ngo = [];
  for (const goc of vanBanOCR.split("\n")) {
    const line = donRac(goc);
    if (line.length < 3) continue;
    const phang = chuan(line);
    const token = line.split(/\s+/);

    // 1. uu tien ma chi so dung o dau dong, vi phieu that in ma truoc
    let code = null, hetTen = 0;
    for (let i = 0; i < Math.min(token.length, 4) && !code; i++) {
      const t = chuan(token[i]).replace(/[^\w%]/g, "");
      const hit = DS_ALIAS.find(([a]) => a.replace(/[^\w%]/g, "") === t);
      if (hit) { code = hit[1]; hetTen = line.indexOf(token[i]) + token[i].length; }
    }
    // 2. neu khong co ma, tim ten dai nhat xuat hien o dau dong
    if (!code) {
      for (const [alias, ma] of DS_ALIAS) {
        const i = phang.indexOf(alias);
        if (i >= 0 && i <= 24) { code = ma; hetTen = i + alias.length; break; }
      }
    }
    if (!code) { boQua.push(line); continue; }

    // 3. doc so dau tien sau ten, va don vi ngay sau no
    const sau = line.slice(Math.min(hetTen, line.length)).split(/\s+/).filter(Boolean);
    let gt = null, dvTho = "";
    for (let i = 0; i < sau.length; i++) {
      if (!/\d/.test(sau[i])) continue;
      const so = laySo(sau[i]);
      if (!so) continue;
      gt = so;
      dvTho = sau[i].endsWith("%") ? "%" : (sau[i + 1] || "");
      break;
    }
    if (gt === null) { boQua.push(line); continue; }

    // 4. chuan hoa don vi, chap nhan cach viet sai thuong gap cua may doc anh
    const kl = chuan(dvTho).replace(/[^\w%^/]/g, "");
    let dv = SUA_DON_VI[kl] || DS_DON_VI.find((u) => chuan(u).replace(/[^\w%^/]/g, "") === kl) || "";

    // 5. cung mot ten co ca dang ty le va dang so luong: chon theo don vi doc duoc
    const doi = (tu, den) => {
      if (code.endsWith(tu) && CHI_SO.some((x) => x.code === code.replace(tu, den))) code = code.replace(tu, den);
    };
    if (dv === "%") doi("_ABS", "_PCT");
    else if (dv) doi("_PCT", "_ABS");

    const a = CHI_SO.find((x) => x.code === code);
    if (!dv && Object.keys(a.quydoi).length === 1) dv = a.dv;
    if (dv && !Object.keys(a.quydoi).some((u) => chuan(u) === chuan(dv))) dv = "";   // don vi khong hop, de trong cho tang 1 tu choi
    dong.push(`${code} ${gt}${dv ? " " + dv : ""}`);

    // 6. canh bao khi con so lech qua xa khoang tham chieu: thuong la may doc sai anh,
    //    vi du mat dau cham thap phan hoac mui ten dinh vao so
    const v = parseFloat(gt);
    if (v > a.cao * 5 || (a.thap > 0 && v < a.thap / 5))
      ngo.push({ code, gt, khoang: `${a.thap}–${a.cao} ${a.dv}`, dong: line });
  }
  return { dong, boQua, ngo };
}

// ---------------------------------------------------------------- TANG 2
const MUC = { BT: "trong_khoang", TD: "theo_doi", KS: "kham_som" };

function tang2(dsNhan) {
  const ket = dsNhan.map((x) => {
    const a = CHI_SO.find((c) => c.code === x.code);
    const bien = a.cao - a.thap;
    let chieu = "trong_khoang", muc = MUC.BT, lech = 0;
    if (x.gt < a.thap) { chieu = "thap"; lech = a.thap - x.gt; }
    else if (x.gt > a.cao) { chieu = "cao"; lech = x.gt - a.cao; }
    if (chieu !== "trong_khoang") muc = lech <= a.hs * bien + 1e-9 ? MUC.TD : MUC.KS;
    return { ...x, thap: a.thap, cao: a.cao, congdung: a.congdung, chieu, muc, lech: +lech.toFixed(3) };
  });
  const nang = ket.some((k) => k.muc === MUC.KS) ? MUC.KS
    : ket.some((k) => k.muc === MUC.TD) ? MUC.TD : MUC.BT;
  return { ket, nhanPhieu: nang };
}

const TEN_MUC = { trong_khoang: "Bình thường", theo_doi: "Nên theo dõi", kham_som: "Nên đi khám sớm" };

// ---------------------------------------------------------------- TANG 3
function taoPrompt(kq) {
  const dong = kq.ket.map((k) =>
    `- ${k.code} (${k.ten}): ${k.goc} | khoảng bình thường ${k.thap}–${k.cao} ${k.dv} | ` +
    `kết luận đã có: ${k.chieu === "trong_khoang" ? "trong khoảng" : k.chieu === "cao" ? "cao hơn bình thường" : "thấp hơn bình thường"}` +
    ` | mức: ${TEN_MUC[k.muc]} | chỉ số này ${k.congdung}`).join("\n");

  return `Bạn viết lại kết quả xét nghiệm cho người bệnh dễ hiểu.

QUY TẮC BẮT BUỘC:
1. Kết luận cao/thấp/bình thường ĐÃ ĐƯỢC TÍNH SẴN. Bạn không được tự đánh giá lại.
2. CẤM nêu tên bệnh, cấm đoán nguyên nhân, cấm nhắc thuốc, liều lượng hay cách điều trị.
3. Mỗi chỉ số viết đúng MỘT câu ngắn, dùng từ thông thường.
4. Trả về đúng JSON theo mẫu, không thêm chữ nào ngoài JSON.

MẪU JSON:
{"items":[{"code":"WBC","explanation":"..."}],"closing":"..."}

DỮ LIỆU:
${dong}

Mức chung của cả phiếu: ${TEN_MUC[kq.nhanPhieu]}.
Câu "closing" nhắc lại mức chung đó, không được nói mọi thứ đều bình thường nếu mức chung khác Bình thường.`;
}

/* Neu goi thang vao Ollama that bai, thu lai qua cau noi o cong ben canh.
   Chrome chan trang https goi vao localhost, cau noi them header de duoc phep. */
let DIA_CHI_DUNG = null;

function diaChiThay(url) {
  if (url.includes(":11434")) return url.replace(":11434", ":11435");
  if (url.includes(":11435")) return url.replace(":11435", ":11434");
  return null;
}

async function goiOllama(url, model, prompt, json = true) {
  const ds = [DIA_CHI_DUNG || url];
  const alt = diaChiThay(ds[0]);
  if (alt) ds.push(alt);
  let loiCuoi = null;
  for (const u of ds) {
    try {
      const r = await goiMot(u, model, prompt, json);
      DIA_CHI_DUNG = u;
      return { ...r, url: u };
    } catch (e) { loiCuoi = e; }
  }
  throw loiCuoi;
}

async function goiMot(url, model, prompt, json = true) {
  const t0 = performance.now();
  const r = await fetch(`${url.replace(/\/+$/, "")}/api/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      model, prompt, stream: false,
      ...(json ? { format: "json" } : {}),
      options: { temperature: 0.2, num_predict: 1200 },
    }),
  });
  if (!r.ok) throw new Error(`Ollama trả về lỗi ${r.status}`);
  const d = await r.json();
  return { text: d.response || "", giay: (performance.now() - t0) / 1000 };
}

// ---------------------------------------------------------------- TANG 4
const TU_CAM = [
  // ten benh neu nhu mot ket luan
  /\bung thu\b/, /\bbach cau cap\b/, /\bsuy tuy\b/, /\bhiv\b/, /\bviem gan\b/,
  /\bsot xuat huyet\b/, /\btieu duong\b/, /\bsuy than\b/, /\bxo gan\b/,
  /\bleukemia\b/, /\bthieu mau\b/,
  // quy nguyen nhan, chan doan
  /\bchan doan\b/, /\bnguyen nhan\b/, /\bdau hieu cua\b/, /\bco the la do\b/,
  /\bco the bi\b/, /\bbi (nhiem trung|viem)\b/, /\bdang (nhiem trung|viem)\b/,
  // thuoc va dieu tri
  /\b(uong|dung|ke|toa) thuoc\b/, /\bkhang sinh\b/, /\bvien uong\b/,
  /\bthuc pham chuc nang\b/, /\bbo sung sat\b/, /\bvitamin\b/, /\bdieu tri\b/,
  /\bphac do\b/, /\btruyen mau\b/, /\blieu dung\b/, /\bnen uong\b/,
  /\d+\s*(mg|ml|vien|lieu)\b/,
];

const TU_TRAN_AN = [
  /\btat ca\b.{0,70}\bbinh thuong\b/, /\b(deu|moi|cac)\s+(chi so|ket qua|xet nghiem)\b.{0,60}\bbinh thuong\b/,
  /\bkhong co (dau hieu|van de|bat thuong)\b/, /\bhoan toan binh thuong\b/, /\bkhong co gi dang lo\b/,
];
const CUM_THAM_CHIEU = [
  /(cao hon|thap hon|vuot|tren|duoi|ngoai|lech|so voi)\s*(khoang|muc|nguong|gioi han|tri so)?\s*binh thuong/g,
  /khoang tham chieu/g,
];
const TU_TRANG_THAI = {
  cao: [/\bcao hon\b/, /\btang cao\b/, /\bvuot\b/, /\btren muc binh thuong\b/, /\bo muc cao\b/],
  thap: [/\bthap hon\b/, /\bgiam\b/, /\bduoi muc binh thuong\b/, /\bo muc thap\b/],
  trong_khoang: [/\bnam trong (khoang|nguong|gioi han)\b/, /\bo muc binh thuong\b/, /\bbinh thuong\b/, /\bon dinh\b/],
};

function tang4(out, kq) {
  const loi = [];
  const coDau = chuan(JSON.stringify(out));
  const items = Array.isArray(out.items) ? out.items : [];
  const maCoTrongPhieu = new Set(kq.ket.map((k) => k.code));
  const maDaViet = new Set();

  for (const it of items) {
    const code = timChiSo(it.code) || String(it.code || "").toUpperCase();
    const chu = chuan(it.explanation || "");
    if (!maCoTrongPhieu.has(code)) { loi.push({ loai: "bịa thêm chỉ số", chi_tiet: code }); continue; }
    maDaViet.add(code);
    const k = kq.ket.find((x) => x.code === code);

    const chuSach = CUM_THAM_CHIEU.reduce((t, re) => t.replace(re, " THAM_CHIEU "), chu);
    for (const [tt, mau] of Object.entries(TU_TRANG_THAI)) {
      if (tt !== k.chieu && mau.some((re) => re.test(chuSach))) {
        loi.push({ loai: "câu chữ nói ngược kết luận", chi_tiet: `${code}: nói "${tt}" nhưng thực tế là "${k.chieu}"` });
        break;
      }
    }
    for (const re of TU_CAM) { const m = chu.match(re); if (m) { loi.push({ loai: "dùng từ bị cấm", chi_tiet: `${code}: "${m[0]}"` }); break; } }
  }
  for (const code of maCoTrongPhieu) if (!maDaViet.has(code)) loi.push({ loai: "bỏ sót chỉ số", chi_tiet: code });

  const closing = chuan(out.closing || "");
  if (kq.nhanPhieu !== MUC.BT && TU_TRAN_AN.some((re) => re.test(closing)))
    loi.push({ loai: "trấn an sai", chi_tiet: "câu kết nói mọi thứ bình thường trên phiếu bất thường" });
  for (const re of TU_CAM) { const m = closing.match(re); if (m) { loi.push({ loai: "dùng từ bị cấm", chi_tiet: `câu kết: "${m[0]}"` }); break; } }
  if (!out.closing) loi.push({ loai: "thiếu câu kết", chi_tiet: "closing rỗng" });

  return { dat: loi.length === 0, loi };
}

function banMau(kq) {
  return {
    items: kq.ket.map((k) => ({
      code: k.code,
      explanation: `${k.ten}: ${k.goc}, khoảng tham chiếu ${k.thap}–${k.cao} ${k.dv}. ` +
        `Kết quả ${k.chieu === "trong_khoang" ? "nằm trong khoảng tham chiếu" : k.chieu === "cao" ? "cao hơn khoảng tham chiếu" : "thấp hơn khoảng tham chiếu"}. ` +
        `Ý nghĩa: ${k.congdung}.`,
    })),
    closing: `Mức chung của cả phiếu: ${TEN_MUC[kq.nhanPhieu]}.`,
  };
}

/* Chay ca bon tang. Sinh lai toi da `soLanToiDa` lan roi moi dung ban mau. */
async function chayPipeline(vanBan, url, model, soLanToiDa, log) {
  const t1 = tang1(vanBan);
  log("tang1", t1);
  if (!t1.nhan.length) return { loi: "Không đọc được chỉ số nào từ phiếu.", t1 };
  const kq = tang2(t1.nhan);
  log("tang2", kq);

  const prompt = taoPrompt(kq);
  let lanCuoi = null, tongGiay = 0;
  for (let lan = 1; lan <= soLanToiDa; lan++) {
    let out, kt;
    try {
      const r = await goiOllama(url, model, prompt, true);
      tongGiay += r.giay;
      out = JSON.parse(r.text);
    } catch (e) {
      lanCuoi = { lan, kt: { dat: false, loi: [{ loai: "không đọc được JSON", chi_tiet: String(e.message || e) }] } };
      log("tang4", lanCuoi);
      continue;
    }
    kt = tang4(out, kq);
    lanCuoi = { lan, out, kt };
    log("tang4", lanCuoi);
    if (kt.dat) return { kq, t1, out, kt, lan, giay: tongGiay, dungBanMau: false };
  }
  return { kq, t1, out: banMau(kq), kt: { dat: true, loi: [] }, lan: soLanToiDa, giay: tongGiay, dungBanMau: true, truot: lanCuoi };
}
