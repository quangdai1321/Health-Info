"""
Test cho tầng 1 + 2.

Tầng 2 là cơ sở an toàn của cả hệ thống, nên độ chính xác phải là 100%.
Con số này được báo cáo trong bài như một tính chất của thiết kế,
không phải kết quả thực nghiệm ngẫu nhiên.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from classifier import ReferenceTable, RuleClassifier, NORMAL, WATCH, URGENT


class TestReferenceTable:
    """Tầng 1: ánh xạ tên chỉ số."""

    def setup_method(self):
        self.t = ReferenceTable()

    def test_bang_khong_rong(self):
        assert len(self.t) >= 20

    def test_khoang_tham_chieu_hop_le(self):
        for a in self.t.analytes.values():
            assert a.low < a.high, f"{a.code}: low phải nhỏ hơn high"
            assert 0 < a.severe_factor <= 1, f"{a.code}: severe_factor ngoài khoảng"

    def test_ma_chuan_tu_khop_chinh_no(self):
        for code in self.t.analytes:
            assert self.t.resolve(code) == code

    def test_bo_dau_tieng_viet(self):
        assert self.t.resolve("so luong bach cau") == "WBC"
        assert self.t.resolve("Số lượng bạch cầu") == "WBC"
        assert self.t.resolve("SỐ LƯỢNG BẠCH CẦU") == "WBC"

    def test_cac_alias_deu_khop(self):
        for a in self.t.analytes.values():
            for alias in a.aliases:
                assert self.t.resolve(alias) == a.code, f"{alias} không khớp {a.code}"

    def test_ten_la_tra_ve_none(self):
        assert self.t.resolve("Chỉ số không tồn tại XYZ") is None


class TestRuleClassifier:
    """Tầng 2: phân loại mức lệch."""

    def setup_method(self):
        self.clf = RuleClassifier()
        self.wbc = self.clf.table.analytes["WBC"]   # 3.4 - 9.4, factor 0.40

    def test_trong_khoang_la_binh_thuong(self):
        for v in (3.4, 5.0, 9.4):
            assert self.clf.classify_one("WBC", v).label == NORMAL

    def test_sat_men_van_binh_thuong(self):
        assert self.clf.classify_one("WBC", self.wbc.low).label == NORMAL
        assert self.clf.classify_one("WBC", self.wbc.high).label == NORMAL

    def test_lech_nhe_la_theo_doi(self):
        span = self.wbc.span
        assert self.clf.classify_one("WBC", self.wbc.high + span * 0.1).label == WATCH
        assert self.clf.classify_one("WBC", self.wbc.low - span * 0.1).label == WATCH

    def test_lech_nhieu_la_kham_som(self):
        span = self.wbc.span
        assert self.clf.classify_one("WBC", self.wbc.high + span * 0.9).label == URGENT

    def test_dung_ngay_tai_nguong(self):
        """Đúng tại severe_factor vẫn là WATCH; vượt qua mới là URGENT."""
        span, f = self.wbc.span, self.wbc.severe_factor
        assert self.clf.classify_one("WBC", self.wbc.high + span * f).label == WATCH
        assert self.clf.classify_one("WBC", self.wbc.high + span * f * 1.01).label == URGENT

    def test_huong_lech(self):
        assert self.clf.classify_one("WBC", 20).direction == "cao"
        assert self.clf.classify_one("WBC", 1).direction == "thap"
        assert self.clf.classify_one("WBC", 5).direction == "trong_khoang"

    def test_bo_qua_gia_tri_trong(self):
        out = self.clf.classify_panel({"WBC": 5.0, "PLT": None, "RBC": ""})
        assert len(out["findings"]) == 1

    def test_ghi_nhan_ten_khong_nhan_ra(self):
        out = self.clf.classify_panel({"WBC": 5.0, "Chỉ số lạ": 1.0})
        assert out["unresolved_names"] == ["Chỉ số lạ"]

    def test_nhan_tong_the_lay_muc_nghiem_trong_nhat(self):
        out = self.clf.classify_panel({"WBC": 5.0, "HGB": (60, "g/L")})
        assert out["overall_label"] == URGENT

    def test_phieu_toan_binh_thuong(self):
        out = self.clf.classify_panel({"WBC": 5.0, "PLT": 250, "RBC": 5.0})
        assert out["overall_label"] == NORMAL
        assert out["abnormal_count"] == 0


class TestBoDuLieuTongHop:
    """Toàn bộ 150 phiếu phải khớp nhãn đích."""

    def test_nhan_dich_khop_hoan_toan(self):
        from generate_data import generate, verify
        panels = generate()
        mismatch, unresolved = verify(panels)
        assert mismatch == 0, f"{mismatch} phiếu lệch nhãn"
        assert unresolved == 0, f"{unresolved} tên chỉ số không nhận ra"

    def test_phan_bo_can_bang(self):
        from generate_data import generate
        panels = generate()
        for lbl in (NORMAL, WATCH, URGENT):
            assert sum(1 for p in panels if p["target_label"] == lbl) == 50


class TestChuanHoaDonVi:
    """
    Tầng chuẩn hóa đơn vị — bổ sung sau khi phát hiện phiếu thật của các
    phòng xét nghiệm khác nhau dùng đơn vị khác nhau cho cùng một chỉ số.
    """

    def setup_method(self):
        from classifier import RuleClassifier, UNKNOWN_UNIT
        self.clf = RuleClassifier()
        self.UNKNOWN = UNKNOWN_UNIT

    def test_quy_doi_g_dL_sang_g_L(self):
        """Hb 14.56 g/dL = 145.6 g/L, nằm trong khoảng bình thường."""
        f = self.clf.classify_one("HGB", 14.56, "g/dL")
        assert f.value == 145.6
        assert f.label == NORMAL
        assert f.converted is True

    def test_khong_quy_doi_thi_bao_dong_gia(self):
        """Nếu bỏ qua đơn vị, cùng giá trị đó bị xếp nhầm thành nghiêm trọng."""
        f = self.clf.classify_one("HGB", 145.6, "g/L")
        assert f.label == NORMAL
        assert f.converted is False

    def test_don_vi_tuong_duong_he_so_1(self):
        """K/µL và G/L là cùng một đại lượng."""
        a = self.clf.classify_one("WBC", 8.977, "K/µL")
        b = self.clf.classify_one("WBC", 8.977, "G/L")
        assert a.value == b.value == 8.977

    def test_ky_tu_micro_khac_nhau(self):
        for u in ("K/µL", "K/μL", "k/ul", "K/uL", " K / µL "):
            assert self.clf.classify_one("WBC", 8.977, u).label == NORMAL

    def test_tu_choi_don_vi_la(self):
        f = self.clf.classify_one("HGB", 14.56, "mmol/L")
        assert f.label == self.UNKNOWN

    def test_tu_choi_khi_thieu_don_vi_neu_nhap_nhang(self):
        """HGB có g/L và g/dL chênh 10 lần nên không được đoán."""
        assert self.clf.classify_one("HGB", 14.56, None).label == self.UNKNOWN

    def test_cho_phep_thieu_don_vi_khi_khong_nhap_nhang(self):
        """MCV chỉ có fL nên thiếu đơn vị vẫn an toàn."""
        assert self.clf.classify_one("MCV", 84.44, None).label == NORMAL

    def test_don_vi_la_khong_lam_hong_nhan_tong_the(self):
        out = self.clf.classify_panel({
            "WBC": (8.977, "K/µL"),
            "Hb": (14.56, "mmol/L"),
        })
        assert out["overall_label"] == NORMAL
        assert len(out["rejected_unknown_unit"]) == 1

    def test_ky_hieu_pct_abs_dat_truoc(self):
        """Phiếu kiểu '% Neu' / '# Neu' phải phân biệt được."""
        t = self.clf.table
        assert t.resolve("% Neu") == "NEUT_PCT"
        assert t.resolve("# Neu") == "NEUT_ABS"
        assert t.resolve("* WBC") == "WBC"

    def test_phieu_that_khong_co_canh_bao_gia(self):
        """Toàn bộ công thức máu của một phiếu thật đều bình thường."""
        out = self.clf.classify_panel({
            "* WBC": (8.977, "K/µL"), "% Neu": (60.05, "%"),
            "% Lym": (26.90, "%"), "% Mono": (8.159, "%"),
            "# Neu": (5.391, "K/µL"), "# Lym": (2.415, "K/µL"),
            "* RBC": (5.212, "M/µL"), "Hb": (14.56, "g/dL"),
            "Hct": (44.01, "%"), "MCV": (84.44, "fL"),
            "MCH": (27.93, "pg"), "MCHC": (33.08, "g/dL"),
            "RDW": (14.03, "%"), "* PLT": (308.7, "K/µL"),
            "MPV": (7.419, "fL"),
        })
        assert out["unresolved_names"] == []
        assert out["rejected_unknown_unit"] == []
        assert out["overall_label"] == NORMAL, \
            f"cảnh báo giả ở: {[f['code'] for f in out['findings'] if f['label'] != NORMAL]}"


class TestBoTuCam:
    """
    Danh sách từ cấm của tầng 4.

    Bổ sung sau khi phát hiện khớp mẫu thô trên tiếng Việt bỏ dấu gây
    dương tính giả: "kích thước" -> "kich thuoc" chứa "thuoc", và
    "nhiễm trùng" là từ vựng hợp lệ khi mô tả chức năng của bạch cầu.
    Lỗi này khiến chính bản mẫu cố định bị đánh trượt.
    """

    def _hit(self, text):
        import re
        from prompt_builder import FORBIDDEN_PATTERNS, _strip_accents
        s = _strip_accents(text)
        return any(re.search(p, s) for p in FORBIDDEN_PATTERNS)

    def test_khong_bat_nham_tu_vung_hop_le(self):
        for t in [
            "Kích thước tiểu cầu đồng đều.",
            "Thể tích trung bình hồng cầu nằm trong khoảng bình thường.",
            "Bạch cầu là tế bào giúp cơ thể chống lại vi khuẩn và nhiễm trùng.",
            "Độ phân bố kích thước hồng cầu.",
        ]:
            assert not self._hit(t), f"bắt nhầm: {t}"

    def test_van_bat_dung_vi_pham_that(self):
        for t in [
            "Đây có thể là dấu hiệu của thiếu máu.",
            "Bạn nên uống thuốc bổ sung sắt.",
            "Uống 500 mg mỗi ngày.",
            "Có thể bị nhiễm trùng.",
            "Nên điều trị theo phác đồ.",
            "Chỉ số này gợi ý ung thư.",
        ]:
            assert self._hit(t), f"bỏ sót: {t}"

    def test_mau_co_dinh_luon_qua_kiem_chung(self):
        """Bản mẫu cố định là đường lui cuối cùng, không được tự vi phạm."""
        from classifier import RuleClassifier
        from prompt_builder import fallback, validate

        clf = RuleClassifier()
        safe = [c for c, a in clf.table.analytes.items()
                if len(set(a.unit_factors.values())) == 1]

        for mode in ("trong_khoang", "ngoai_khoang"):
            vals = {
                c: (clf.table.analytes[c].low + 0.1 if mode == "trong_khoang"
                    else clf.table.analytes[c].high * 3)
                for c in safe
            }
            cl = clf.classify_panel(vals)
            v = validate(fallback(cl), cl)
            assert v["passed"], f"{mode}: mẫu cố định vi phạm {v['violations'][:2]}"


class TestDoMauThuan:
    """
    Kiểm tra mâu thuẫn giữa câu chữ và trạng thái đã xác định.

    Bổ sung sau khi phát hiện dương tính giả loại thứ hai: cụm "bình thường"
    có hai vai trò khác nhau — chỉ trạng thái của chỉ số, hoặc chỉ khoảng
    tham chiếu. Câu "cao hơn khoảng bình thường" là đúng cho chỉ số cao,
    nhưng ban đầu bị báo là mâu thuẫn vì chứa từ "bình thường".
    """

    def _contradicts(self, direction, text):
        import re
        from prompt_builder import STATUS_WORDS, _strip_accents, _strip_reference_phrases
        s = _strip_reference_phrases(_strip_accents(text))
        return any(
            any(re.search(p, s) for p in pats)
            for other, pats in STATUS_WORDS.items() if other != direction
        )

    def test_cho_qua_khi_nhac_khoang_tham_chieu(self):
        """Nhắc 'bình thường' như một mốc so sánh thì không phải mâu thuẫn."""
        for d, t in [
            ("cao", "Chỉ số này đang cao hơn khoảng bình thường."),
            ("cao", "Giá trị vượt ngưỡng bình thường một chút."),
            ("thap", "Chỉ số này thấp hơn mức bình thường."),
            ("thap", "Giá trị nằm dưới khoảng bình thường."),
            ("trong_khoang", "Chỉ số này nằm trong khoảng bình thường."),
        ]:
            assert not self._contradicts(d, t), f"bắt nhầm [{d}]: {t}"

    def test_van_bat_mau_thuan_that(self):
        """Khẳng định trạng thái sai thì phải bị chặn."""
        for d, t in [
            ("cao", "Chỉ số này đang ở mức bình thường."),
            ("cao", "Kết quả bình thường, không cần lo lắng."),
            ("cao", "Kết quả ổn định."),
            ("thap", "Chỉ số này cao hơn ngưỡng cho phép."),
            ("trong_khoang", "Chỉ số này thấp hơn mức cần thiết."),
        ]:
            assert self._contradicts(d, t), f"bỏ sót [{d}]: {t}"


class TestValidateDaVa:
    """Ba bản vá cho tầng 4 sau khi soi kết quả chạy thật."""

    def setup_method(self):
        from classifier import RuleClassifier
        self.clf = RuleClassifier()
        self.c = self.clf.classify_panel({
            "WBC": 5.0, "PLT": 245, "HGB": (100, "g/L"),
        })

    def _types(self, out):
        from prompt_builder import validate
        return [v["type"] for v in validate(out, self.c)["violations"]]

    def test_ten_hien_thi_khong_bi_tinh_la_bia(self):
        """Mô hình điền 'SLBC' thay vì 'WBC' là lỗi định dạng, không phải bịa."""
        out = {"items": [
            {"code": "SLBC", "plain_name": "x", "status": "trong_khoang",
             "explanation": "nam trong khoang binh thuong"},
            {"code": "Số lượng tiểu cầu", "plain_name": "x", "status": "trong_khoang",
             "explanation": "nam trong khoang binh thuong"},
            {"code": "Hb", "plain_name": "x", "status": "thap",
             "explanation": "thap hon khoang binh thuong"},
        ], "closing": "Mang kết quả đến bác sĩ."}
        types = self._types(out)
        assert "hallucinated_analyte" not in types
        assert "missing_analyte" not in types
        assert types.count("code_format") == 3

    def test_bia_that_van_bi_bat(self):
        out = {"items": [
            {"code": "KHONG_TON_TAI_XYZ", "plain_name": "x", "status": "cao",
             "explanation": "x"},
        ], "closing": "x"}
        assert "hallucinated_analyte" in self._types(out)

    def test_tran_an_sai_o_phieu_bat_thuong(self):
        """Phiếu có HGB thấp mà câu kết nói mọi thứ bình thường."""
        out = {"items": [
            {"code": "WBC", "plain_name": "x", "status": "trong_khoang",
             "explanation": "nam trong khoang binh thuong"},
            {"code": "PLT", "plain_name": "x", "status": "trong_khoang",
             "explanation": "nam trong khoang binh thuong"},
            {"code": "HGB", "plain_name": "x", "status": "thap",
             "explanation": "thap hon khoang binh thuong"},
        ], "closing": "Tất cả các kết quả xét nghiệm đều nằm trong khoảng bình thường."}
        assert "false_reassurance" in self._types(out)

    def test_khong_bao_tran_an_o_phieu_binh_thuong(self):
        """Cùng câu đó nhưng phiếu thật sự bình thường thì không phải lỗi."""
        from prompt_builder import validate
        c = self.clf.classify_panel({"WBC": 5.0, "PLT": 245})
        out = {"items": [
            {"code": "WBC", "plain_name": "x", "status": "trong_khoang",
             "explanation": "nam trong khoang binh thuong"},
            {"code": "PLT", "plain_name": "x", "status": "trong_khoang",
             "explanation": "nam trong khoang binh thuong"},
        ], "closing": "Tất cả các kết quả đều nằm trong khoảng bình thường."}
        types = [v["type"] for v in validate(out, c)["violations"]]
        assert "false_reassurance" not in types

    def test_cau_ket_hop_le_khong_bi_bat(self):
        out = {"items": [
            {"code": "WBC", "plain_name": "x", "status": "trong_khoang",
             "explanation": "nam trong khoang binh thuong"},
            {"code": "PLT", "plain_name": "x", "status": "trong_khoang",
             "explanation": "nam trong khoang binh thuong"},
            {"code": "HGB", "plain_name": "x", "status": "thap",
             "explanation": "thap hon khoang binh thuong"},
        ], "closing": "Một số chỉ số nằm ngoài khoảng tham chiếu, hãy hỏi bác sĩ."}
        assert self._types(out) == []
