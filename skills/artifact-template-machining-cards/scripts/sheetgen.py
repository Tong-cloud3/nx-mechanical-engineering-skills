# -*- coding: utf-8 -*-
"""AutoLISP sheet generator: A4 landscape operation sketches (297 x 210 mm, 1:1)."""
import math

def ls(text):
    return '"' + str(text).replace('\\', '/').replace('"', "'") + '"'

def n(v):
    if isinstance(v, int):
        return str(v)
    return ('%.3f' % float(v)).rstrip('0').rstrip('.')

COMMON = r'''
(defun EMK (lst / r)
  (setq r (vl-catch-all-apply 'entmake (list lst)))
  (if (vl-catch-all-error-p r)
    (princ (strcat "\nENTERR " (cdr (assoc 0 lst)) ": " (vl-catch-all-error-message r))))
  r)
(defun mk-layer (name color lw lt)
  (if (not (tblsearch "LAYER" name))
    (EMK (list '(0 . "LAYER") '(100 . "AcDbSymbolTableRecord") '(100 . "AcDbLayerTableRecord")
               (cons 2 name) '(70 . 0) (cons 62 color) (cons 370 lw) (cons 6 lt)))))
(defun mk-style (name font width)
  (if (not (tblsearch "STYLE" name))
    (EMK (list '(0 . "STYLE") '(100 . "AcDbSymbolTableRecord") '(100 . "AcDbTextStyleTableRecord")
               (cons 2 name) '(70 . 0) '(40 . 0.0) (cons 41 width) '(50 . 0.0)
               '(71 . 0) '(42 . 3.5) (cons 3 font) '(4 . "")))))
(defun L (x1 y1 x2 y2)
  (EMK (list '(0 . "LINE") (cons 8 (getvar "CLAYER"))
             (cons 10 (list (float x1) (float y1) 0.0))
             (cons 11 (list (float x2) (float y2) 0.0)))))
(defun C (x y r)
  (EMK (list '(0 . "CIRCLE") (cons 8 (getvar "CLAYER"))
             (cons 10 (list (float x) (float y) 0.0)) (cons 40 (float r)))))
(defun A (x y r a1 a2)
  (EMK (list '(0 . "ARC") (cons 8 (getvar "CLAYER"))
             (cons 10 (list (float x) (float y) 0.0)) (cons 40 (float r))
             (cons 50 (float a1)) (cons 51 (float a2)))))
(defun T (x y h s j)
  (EMK (list '(0 . "TEXT") (cons 8 (getvar "CLAYER"))
             (cons 10 (list (float x) (float y) 0.0)) (cons 40 (float h))
             (cons 1 s) (cons 7 "CNB") (cons 72 j) '(73 . 2)
             (cons 11 (list (float x) (float y) 0.0)))))
(defun SOLID (x1 y1 x2 y2 x3 y3 x4 y4)
  (EMK (list '(0 . "SOLID") (cons 8 (getvar "CLAYER")) '(62 . 7)
             (cons 10 (list (float x1) (float y1) 0.0))
             (cons 11 (list (float x2) (float y2) 0.0))
             (cons 12 (list (float x3) (float y3) 0.0))
             (cons 13 (list (float x4) (float y4) 0.0)))))
(defun FILLR (x1 y1 x2 y2)
  (setvar "CLAYER" "FILL")
  (EMK (list '(0 . "SOLID") '(8 . "FILL") '(62 . 254)
             (cons 10 (list (float x1) (float y1) 0.0))
             (cons 11 (list (float x2) (float y1) 0.0))
             (cons 12 (list (float x1) (float y2) 0.0))
             (cons 13 (list (float x2) (float y2) 0.0))))
  (setvar "CLAYER" "OUTLINE"))
(defun RECT (x1 y1 x2 y2)
  (L x1 y1 x2 y1) (L x2 y1 x2 y2) (L x2 y2 x1 y2) (L x1 y2 x1 y1))
(defun DASHRECT (x1 y1 x2 y2)
  (setvar "CLAYER" "STOCK") (RECT x1 y1 x2 y2) (setvar "CLAYER" "OUTLINE"))
(defun ARROWTRI (xt yt xb yb w)
  (setq ang (angle (list xt yt) (list xb yb)))
  (setq bc (polar (list xt yt) ang w))
  (setq p1 (polar bc (+ ang 1.5707963) w)
        p2 (polar bc (- ang 1.5707963) w))
  (EMK (list '(0 . "SOLID") (cons 8 (getvar "CLAYER")) '(62 . 7)
             (cons 10 (list (float xt) (float yt) 0.0))
             (cons 11 (list (float (car p1)) (float (cadr p1)) 0.0))
             (cons 12 (list (float (car p2)) (float (cadr p2)) 0.0))
             (cons 13 (list (float (car p2)) (float (cadr p2)) 0.0)))))
(defun ARROW (x1 y1 x2 y2 sz)
  (L x1 y1 x2 y2)
  (ARROWTRI x2 y2 x1 y1 (* sz 0.36)))
(defun LEADER (tx ty px py txt)
  (setvar "CLAYER" "DIM") (L tx ty px py) (ARROWTRI px py tx ty 1.4)
  (setvar "CLAYER" "TEXT") (T tx (+ ty 1.4) 3.1 txt 1))
(defun DIMH (x1 x2 yf yd txt)
  (setvar "CLAYER" "DIM")
  (L x1 yf x1 (+ yd 1.8)) (L x2 yf x2 (+ yd 1.8)) (L x1 yd x2 yd)
  (ARROWTRI x1 yd (+ x1 7) yd 1.3) (ARROWTRI x2 yd (- x2 7) yd 1.3)
  (setvar "CLAYER" "TEXT") (T (/ (+ x1 x2) 2.0) (+ yd 1.6) 3.4 txt 1))
(defun DIMV (y1 y2 xf xd txt side ty)
  (setvar "CLAYER" "DIM")
  (if (< xd xf)
    (progn (L xf y1 (- xd 1.8) y1) (L xf y2 (- xd 1.8) y2))
    (progn (L xf y1 (+ xd 1.8) y1) (L xf y2 (+ xd 1.8) y2)))
  (L xd y1 xd y2)
  (ARROWTRI xd y1 xd (+ y1 7) 1.3) (ARROWTRI xd y2 xd (- y2 7) 1.3)
  (setvar "CLAYER" "TEXT")
  (if (= side 2)
    (T (- xd 1.6) ty 3.4 txt 2)
    (T (+ xd 1.6) ty 3.4 txt 0)))
(defun SUP (x y w)
  (setvar "CLAYER" "FIXTURE")
  (L (- x w) (- y 4) (+ x w) (- y 4))
  (L (- x (* w 0.55)) (- y 4) x y)
  (L (+ x (* w 0.55)) (- y 4) x y)
  (L (- x (* w 0.8)) (- y 4) (+ x (* w 0.8)) (- y 4))
  (setvar "CLAYER" "OUTLINE"))
(defun CLAMP (x y)
  (setvar "CLAYER" "FIXTURE")
  (L x (+ y 19) x (+ y 3))
  (L (- x 5) (+ y 19) (+ x 5) (+ y 19))
  (L (- x 5) (+ y 19) (- x 5) (+ y 14))
  (L (+ x 5) (+ y 19) (+ x 5) (+ y 14))
  (ARROWTRI x y x (+ y 9) 1.7)
  (setvar "CLAYER" "OUTLINE"))
(defun CLAMPSIDE (x y dir)
  (setvar "CLAYER" "FIXTURE")
  (L (- x (* dir 15)) y (- x (* dir 3)) y)
  (L (- x (* dir 15)) (- y 7) (- x (* dir 15)) (+ y 7))
  (L (- x (* dir 15)) (+ y 7) (- x (* dir 21)) (+ y 7))
  (L (- x (* dir 15)) (- y 7) (- x (* dir 21)) (- y 7))
  (ARROWTRI x y (- x (* dir 9)) y 1.7)
  (setvar "CLAYER" "OUTLINE"))
(defun CENTERH (x1 x2 y)
  (setvar "CLAYER" "CENTER") (L x1 y x2 y)
  (setvar "CLAYER" "OUTLINE"))
(defun CENTERV (x y1 y2)
  (setvar "CLAYER" "CENTER") (L x y1 x y2)
  (setvar "CLAYER" "OUTLINE"))
(defun ROUGH (x y s)
  (setvar "CLAYER" "TEXT")
  (L (- x 5) (- y 4) x y) (L x y (+ x 5) (- y 4)) (L (- x 6) (- y 4) (+ x 6) (- y 4))
  (T (+ x 8) (+ y 1) 2.8 s 0)
  (setvar "CLAYER" "OUTLINE"))
(defun SECLABEL (x1 y1 x2 y2 a b)
  (setvar "CLAYER" "DIM")
  (L x1 y1 (- x1 8) y1) (L x2 y2 (- x2 8) y2)
  (ARROWTRI (- x1 8) y1 x1 y1 1.6) (ARROWTRI (- x2 8) y2 x2 y2 1.6)
  (setvar "CLAYER" "TEXT")
  (T (- x1 13) y1 3.6 a 1) (T (- x2 13) y2 3.6 b 1)
  (setvar "CLAYER" "OUTLINE"))
(defun FRAME (scale_txt part opno opname dwgno sht)
  (setvar "CLAYER" "FRAME")
  (RECT 10 10 287 200)
  (RECT 14 14 283 196)
  (L 14 40 283 40)
  (L 150 40 150 14)
  (L 150 27 283 27)
  (L 196 14 196 27)
  (L 232 14 232 27)
  (setvar "CLAYER" "TITLE")
  (T 154 35.6 3.4 part 0)
  (T 154 31.0 3.2 (strcat "工序 " opno "   " opname) 0)
  (T 280 36.0 2.8 (strcat "图号 " dwgno) 2)
  (T 280 31.6 2.7 (strcat "比例 " scale_txt "   单位 mm") 2)
  (T 154 22 2.6 "设计" 0) (T 166 22 2.6 "工艺组" 0)
  (T 200 22 2.6 "审核" 0) (T 212 22 2.6 "—" 0)
  (T 240 22 2.6 "日期" 0) (T 252 22 2.6 "2026-11" 0)
  (T 154 17.2 2.6 (strcat "图幅 A4    第 " (itoa sht) " 张    机械制造工艺课程设计") 0)
  (T 18 35.0 2.7 "图例：虚线 = 被遮挡轮廓   双点划线 = 毛坯/前工序轮廓" 0)
  (T 18 30.2 2.7 "点划线 = 中心线/对称线   45°细线 = 加工余量/剖面线" 0)
  (T 18 25.4 2.7 "人字∧+基面=定位支承  圆点尾箭头=夹紧  方框字母=基准" 0)
  (T 18 20.6 2.7 "简图仅表示本工序加工内容、装夹与测量基准，不替代零件图。" 0)
  (T 18 16.0 2.7 "尺寸单位 mm；公差、圆角与表面要求按零件图样。" 0)
  (setvar "CLAYER" "OUTLINE"))
(defun CLEAR-SHEET ()
  (if (ssget "_X") (command "_.ERASE" "_ALL" ""))
  (setvar "CLAYER" "OUTLINE") (setvar "OSMODE" 0) (setvar "FILLMODE" 1)
  (setvar "LWDISPLAY" 1) (setvar "LTSCALE" 1.0) (setvar "CELTSCALE" 1.0)
  (setvar "CECOLOR" "BYLAYER"))
(defun INIT ()
  (command "_.-LINETYPE" "_L" "DASHED" "acadiso.lin" "")
  (command "_.-LINETYPE" "_L" "DASHDOT" "acadiso.lin" "")
  (command "_.-LINETYPE" "_L" "CENTER" "acadiso.lin" "")
  (command "_.-LINETYPE" "_L" "PHANTOM" "acadiso.lin" "")
  (mk-style "CNB" "simhei.ttf" 0.72)
  (mk-layer "FRAME" 7 50 "Continuous")
  (mk-layer "TITLE" 7 30 "Continuous")
  (mk-layer "OUTLINE" 7 45 "Continuous")
  (mk-layer "THIN" 7 20 "Continuous")
  (mk-layer "STOCK" 8 20 "PHANTOM")
  (mk-layer "HIDDEN" 8 18 "DASHED")
  (mk-layer "CENTER" 8 13 "CENTER")
  (mk-layer "FILL" 254 9 "Continuous")
  (mk-layer "FIXTURE" 7 35 "Continuous")
  (mk-layer "TOOL" 7 45 "Continuous")
  (mk-layer "DIM" 7 18 "Continuous")
  (mk-layer "TEXT" 7 18 "Continuous")
  (mk-layer "WARN" 1 30 "Continuous")
  (setvar "FILLMODE" 1) (setvar "LWDISPLAY" 1)
  (setvar "OSMODE" 0) (setvar "CLAYER" "OUTLINE"))
(defun SAVEPLOT (stem / dwg pdf)
  (setq dwg (strcat OUTDIR stem ".dwg") pdf (strcat OUTDIR stem ".pdf"))
  (if (findfile dwg) (vl-file-delete dwg))
  (if (findfile pdf) (vl-file-delete pdf))
  (command "_.ZOOM" "_E")
  (command "_.SAVEAS" "2018" dwg)
  (command "_.-PLOT" "Y" "Model" "DWG To PDF.pc3" "ISO A4 (297.00 x 210.00 毫米)"
           "M" "L" "N" "E" "F" "C" "Y" "." "Y" "W" pdf "N" "Y")
  (princ (strcat "\nSAVED " stem " n=" (itoa (sslength (ssget "_X"))))))
'''

class Sheet:
    def __init__(self, stem, part, opno, opname, dwgno, scale_txt='1:1', sht=1):
        self.stem = stem
        self.part = part
        self.opno = opno
        self.opname = opname
        self.dwgno = dwgno
        self.scale = scale_txt
        self.sht = sht
        self.lines = []
        self.k = 1.0
        self.ox = 0.0
        self.oy = 0.0
        self.texts = []   # absolute boxes for collision checking
        self.hatch = []   # filled/hatched regions (bad under text)
        self.circles = [] # hole/tool circles (bad under text)
        self.edges = []   # outline segments (text should not cross)
        self.segs = []    # every drawn segment (a, b, layer) for overlap checks

    def set_view(self, k, ox, oy):
        self.k, self.ox, self.oy = float(k), float(ox), float(oy)

    def P(self, x, y):
        return (self.ox + x * self.k, self.oy + y * self.k)

    # --- primitives -----------------------------------------------------
    def add(self, s):
        self.lines.append(s)

    def L(self, x1, y1, x2, y2, layer='OUTLINE'):
        a, b = self.P(x1, y1), self.P(x2, y2)
        if layer in ('OUTLINE', 'STOCK'):
            self.edges.append((min(a[0], b[0]) - 0.4, min(a[1], b[1]) - 0.4,
                               max(a[0], b[0]) + 0.4, max(a[1], b[1]) + 0.4))
        self.segs.append((a, b, layer))
        self.add('(setvar "CLAYER" %s)(L %s %s %s %s)' % (ls(layer), n(a[0]), n(a[1]), n(b[0]), n(b[1])))

    def C(self, x, y, r, layer='OUTLINE'):
        a = self.P(x, y)
        rr = r * self.k
        self.circles.append((a[0] - rr, a[1] - rr, a[0] + rr, a[1] + rr))
        self.add('(setvar "CLAYER" %s)(C %s %s %s)' % (ls(layer), n(a[0]), n(a[1]), n(rr)))

    def A(self, x, y, r, a1, a2, layer='OUTLINE'):
        a = self.P(x, y)
        self.add('(setvar "CLAYER" %s)(A %s %s %s %s %s)' % (ls(layer), n(a[0]), n(a[1]), n(r * self.k), n(a1), n(a2)))

    def T(self, x, y, h, s, j=0, layer='TEXT'):
        a = self.P(x, y)
        self._track(a[0], a[1], h, s, j)
        self.add('(setvar "CLAYER" %s)(T %s %s %s %s %d)' % (ls(layer), n(a[0]), n(a[1]), n(h), ls(s), j))

    def _track(self, x, y, h, txt, j):
        # Measured from rendered PDFs: CJK advance ~1.763*h, latin ~0.88*h.
        w = h * sum(1.763 if ord(c) > 0x2000 else 0.88 for c in str(txt))
        x0 = x if j == 0 else (x - w / 2.0 if j == 1 else x - w)
        self.texts.append((x0, y - h / 2.0, x0 + w, y + h / 2.0, str(txt)))

    def RECT(self, x1, y1, x2, y2, layer='OUTLINE'):
        a, b = self.P(x1, y1), self.P(x2, y2)
        self.add('(setvar "CLAYER" %s)(RECT %s %s %s %s)' % (ls(layer), n(a[0]), n(a[1]), n(b[0]), n(b[1])))

    def DASHRECT(self, x1, y1, x2, y2):
        for px1, py1, px2, py2 in ((x1, y1, x2, y1), (x2, y1, x2, y2),
                                   (x2, y2, x1, y2), (x1, y2, x1, y1)):
            self.L(px1, py1, px2, py2, 'STOCK')

    def FILLR(self, x1, y1, x2, y2):
        a, b = self.P(x1, y1), self.P(x2, y2)
        self.hatch.append((min(a[0], b[0]), min(a[1], b[1]), max(a[0], b[0]), max(a[1], b[1])))
        self.add('(FILLR %s %s %s %s)' % (n(a[0]), n(a[1]), n(b[0]), n(b[1])))

    def POLY(self, pts, close=True, layer='OUTLINE'):
        pts = list(pts)
        for i in range(len(pts) - 1):
            self.L(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], layer)
        if close and len(pts) > 2:
            self.L(pts[-1][0], pts[-1][1], pts[0][0], pts[0][1], layer)

    def HATCH(self, x1, y1, x2, y2, gap=3.2, layer='THIN'):
        """45-degree section lines clipped to the rectangle."""
        a, b = self.P(x1, y1), self.P(x2, y2)
        self.hatch.append((min(a[0], b[0]), min(a[1], b[1]), max(a[0], b[0]), max(a[1], b[1])))
        w, h = x2 - x1, y2 - y1
        t = -h
        while t < w:
            k0 = max(0.0, -t)
            k1 = min(h, w - t)
            if k1 - k0 > 0.02:
                self.L(x1 + t + k0, y1 + k0, x1 + t + k1, y1 + k1, layer)
            t += gap

    def ARROW(self, x1, y1, x2, y2, sz=5):
        a, b = self.P(x1, y1), self.P(x2, y2)
        self.add('(setvar "CLAYER" "TOOL")(ARROW %s %s %s %s %s)' % (n(a[0]), n(a[1]), n(b[0]), n(b[1]), n(sz)))

    def LEADER(self, tx, ty, px, py, text):
        a, b = self.P(tx, ty), self.P(px, py)
        self._track(a[0], a[1] + 1.4, 3.1, text, 1)
        self.add('(LEADER %s %s %s %s %s)' % (n(a[0]), n(a[1]), n(b[0]), n(b[1]), ls(text)))

    def DIMH(self, x1, x2, yf, yd, text):
        a, b, c, d = self.P(x1, yf), self.P(x2, yf), self.P(x1, yd), self.P(x2, yd)
        self._track((a[0] + b[0]) / 2.0, c[1] + 1.6, 3.4, text, 1)
        self.add('(DIMH %s %s %s %s %s)' % (n(a[0]), n(b[0]), n(a[1]), n(c[1]), ls(text)))

    def DIMV(self, y1, y2, xf, xd, text, side=0, ty=None):
        a, b, c, d = self.P(xf, y1), self.P(xf, y2), self.P(xd, y1), self.P(xd, y2)
        mid = (a[1] + b[1]) / 2.0
        if side == 2:
            self._track(c[0] - 1.6, mid if ty is None else ty, 3.4, text, 2)
        else:
            self._track(c[0] + 1.6, mid if ty is None else ty, 3.4, text, 0)
        self.add('(DIMV %s %s %s %s %s %d %s)' % (n(a[1]), n(b[1]), n(a[0]), n(c[0]), ls(text), side,
                                                  n(mid if ty is None else ty)))

    # --- raw (sheet-coordinate) emit helpers ----------------------------
    def _line(self, a, b, layer='OUTLINE'):
        self.segs.append((a, b, layer))
        self.add('(setvar "CLAYER" %s)(L %s %s %s %s)'
                 % (ls(layer), n(a[0]), n(a[1]), n(b[0]), n(b[1])))

    def _solid(self, p1, p2, p3, layer='FIXTURE'):
        self.add('(setvar "CLAYER" %s)(SOLID %s %s %s %s %s %s %s %s)'
                 % (ls(layer), n(p1[0]), n(p1[1]), n(p2[0]), n(p2[1]),
                    n(p3[0]), n(p3[1]), n(p3[0]), n(p3[1])))

    def _arrowhead(self, tip, tail, w, layer='TOOL'):
        dx, dy = tip[0] - tail[0], tip[1] - tail[1]
        ln = math.hypot(dx, dy) or 1.0
        ux, uy = dx / ln, dy / ln
        vx, vy = -uy, ux
        bx, by = tip[0] - ux * w, tip[1] - uy * w
        p1 = (bx + vx * w, by + vy * w)
        p2 = (bx - vx * w, by - vy * w)
        self._solid(tip, p1, p2, layer)

    def _rect_raw(self, x1, y1, x2, y2, layer='DIM'):
        self._line((x1, y1), (x2, y1), layer)
        self._line((x2, y1), (x2, y2), layer)
        self._line((x2, y2), (x1, y2), layer)
        self._line((x1, y2), (x1, y1), layer)

    def SUP(self, x, y, w=6, direction=0):
        """JB/T 5061 fixed locating support: solid triangle + hatched ground line.

        direction: 0 = support from below (contact face above), 1 = from left,
        2 = from right, 3 = from above.  The given point is the contact point."""
        self.support_sym(x, y, direction)

    def support_sym(self, x, y, direction=0, kind='fixed'):
        """JB/T 5061 定位支承符号（标注在视图轮廓线上）。

        图形：人字两腿自接触点向下，脚端各向外折一段短横线（脚间空开）；
        活动式/辅助支承的两腿中段为波纹，辅助支承另加中部横贯线。
        """
        a = self.P(x, y)
        h, w, foot = 7.0, 3.4, 3.0
        ux, uy = ((0, 1), (1, 0), (-1, 0), (0, -1))[direction]
        vx, vy = -uy, ux
        for sgn in (1, -1):
            foot_p = (a[0] - ux * h + vx * w * sgn, a[1] - uy * h + vy * w * sgn)
            if kind == 'fixed':
                self._line(a, foot_p, 'FIXTURE')
            else:
                p1 = (a[0] * 0.66 + foot_p[0] * 0.34, a[1] * 0.66 + foot_p[1] * 0.34)
                p2 = (a[0] * 0.34 + foot_p[0] * 0.66, a[1] * 0.34 + foot_p[1] * 0.66)
                self._line(a, p1, 'FIXTURE')
                z1 = (p1[0] - vx * 1.6 * sgn - ux * 1.1, p1[1] - vy * 1.6 * sgn - uy * 1.1)
                z2 = (p2[0] - vx * 1.6 * sgn + ux * 1.1, p2[1] - vy * 1.6 * sgn + uy * 1.1)
                self._line(p1, z1, 'FIXTURE')
                self._line(z1, z2, 'FIXTURE')
                self._line(z2, p2, 'FIXTURE')
                self._line(p2, foot_p, 'FIXTURE')
            # 脚端外折短横线
            base_p = (foot_p[0] + vx * foot * sgn, foot_p[1] + vy * foot * sgn)
            self._line(foot_p, base_p, 'FIXTURE')
        if kind == 'aux':
            c = (a[0] - ux * h * 0.52, a[1] - uy * h * 0.52)
            self._line((c[0] + vx * w * 1.55, c[1] + vy * w * 1.55),
                       (c[0] - vx * w * 1.55, c[1] - vy * w * 1.55), 'FIXTURE')

    def SUP(self, x, y, w=6, direction=0, kind='fixed'):
        self.support_sym(x, y, direction, kind)

    def CLAMP(self, x, y, direction=3, length=16.0):
        """JB/T 5061 手动夹紧符号：尾端小圆点 + 直线段 + 箭头指向夹紧面。"""
        self.clamp_sym(x, y, direction, length)

    def clamp_sym(self, x, y, direction=3, length=16.0):
        a = self.P(x, y)
        ux, uy = ((0, 1), (1, 0), (-1, 0), (0, -1))[direction]
        tail = (a[0] - ux * length, a[1] - uy * length)
        self._line(tail, a, 'FIXTURE')
        self._arrowhead(a, tail, 2.4, 'FIXTURE')
        self._dot(tail, 0.95, 'FIXTURE')

    def CLAMPSIDE(self, x, y, direction):
        self.clamp_sym(x, y, 1 if direction > 0 else 2)

    def locate_face(self, x, y):
        """JB/T 5061 定位点标注在视图正面上：圆圈中一点。"""
        a = self.P(x, y)
        self.circles.append((a[0] - 1.7, a[1] - 1.7, a[0] + 1.7, a[1] + 1.7))
        self.add('(setvar "CLAYER" "FIXTURE")(C %s %s 1.7)' % (n(a[0]), n(a[1])))
        self._dot(a, 0.55, 'FIXTURE')

    def _dot(self, c, r, layer='FIXTURE'):
        self.add('(setvar "CLAYER" %s)(C %s %s %s)' % (ls(layer), n(c[0]), n(c[1]), n(r)))

    def DATUM(self, x, y, letter, direction=3, off=12.0):
        """GB/T 1182 datum feature symbol: solid triangle + leader + boxed letter."""
        a = self.P(x, y)
        ux, uy = ((0, 1), (1, 0), (-1, 0), (0, -1))[direction]
        vx, vy = -uy, ux
        w, h = 2.2, 3.4
        base = (a[0] - ux * h, a[1] - uy * h)
        self._solid(a, (base[0] + vx * w, base[1] + vy * w), (base[0] - vx * w, base[1] - vy * w), 'FIXTURE')
        tip = (a[0] - ux * off, a[1] - uy * off)
        self._line(base, tip, 'DIM')
        bx, by = tip[0] - ux * 3.5, tip[1] - uy * 3.5
        self._rect_raw(bx - 3.5, by - 3.5, bx + 3.5, by + 3.5, 'DIM')
        self.RT(bx, by, 3.4, letter, 1, 'TEXT')

    def CENTERH(self, x1, x2, y):
        a, b = self.P(x1, y), self.P(x2, y)
        self.segs.append((a, b, 'CENTER'))
        self.add('(CENTERH %s %s %s)' % (n(a[0]), n(b[0]), n(a[1])))

    def CENTERV(self, x, y1, y2):
        a, b = self.P(x, y1), self.P(x, y2)
        self.segs.append((a, b, 'CENTER'))
        self.add('(CENTERV %s %s %s)' % (n(a[0]), n(a[1]), n(b[1])))

    def ROUGH(self, x, y, s):
        a = self.P(x, y)
        self.add('(ROUGH %s %s %s)' % (n(a[0]), n(a[1]), ls(s)))

    def SECLABEL(self, x1, y1, x2, y2, a, b):
        p, q = self.P(x1, y1), self.P(x2, y2)
        self.add('(SECLABEL %s %s %s %s %s %s)' % (n(p[0]), n(p[1]), n(q[0]), n(q[1]), ls(a), ls(b)))

    # --- assembly -------------------------------------------------------
    def RT(self, x, y, h, txt, j=0, layer='TEXT'):
        self._track(x, y, h, txt, j)
        self.add('(setvar "CLAYER" %s)(T %s %s %s %s %d)' % (ls(layer), n(x), n(y), n(h), ls(txt), j))

    def begin(self, framed=True):
        head = ['(CLEAR-SHEET)']
        if framed:
            head.append('(FRAME %s %s %s %s %s %d)' % (ls(self.scale), ls(self.part), ls(self.opno),
                                                      ls(self.opname), ls(self.dwgno), self.sht))
        self.lines = head + self.lines


def _ov(a, b):
    ox = min(a[2], b[2]) - max(a[0], b[0])
    oy = min(a[3], b[3]) - max(a[1], b[1])
    return ox * oy if (ox > 0.4 and oy > 0.4) else 0.0


def collisions(sheets):
    """Return list of (sheet, kind, detail) for text-text/text-geometry clashes."""
    out = []
    for s in sheets:
        ts = s.texts
        for i in range(len(ts)):
            for j in range(i + 1, len(ts)):
                a, b = ts[i], ts[j]
                if _ov(a, b):
                    out.append((s.stem, '文字-文字', '%s  ×  %s' % (a[4], b[4])))
        for t in ts:
            if t[0] < 12 or t[2] > 285 or t[1] < 12 or t[3] > 198:
                out.append((s.stem, '越界', t[4]))
                continue
            for h in s.hatch:
                if _ov(t, h) > 1.5:
                    out.append((s.stem, '文字压剖面线', t[4]))
                    break
            for c in s.circles:
                if _ov(t, c) > 1.5:
                    out.append((s.stem, '文字压孔', t[4]))
                    break
            for e in s.edges:
                if _ov(t, e) > 1.0:
                    out.append((s.stem, '文字穿轮廓', t[4]))
                    break
    return out


def build_lisp(out_lisp, outdir, sheets, framed=True):
    funcs, calls = [], []
    for i, s in enumerate(sheets, start=1):
        s.begin(framed)
        name = 'D%03d' % i
        funcs.append('(defun c:%s ()\n%s\n(princ))' % (name, '\n'.join(s.lines)))
        calls.append('(c:%s)(SAVEPLOT %s)' % (name, ls(s.stem)))
    code = ['(setq OUTDIR %s)' % ls(outdir.replace('\\', '/')), COMMON,
            '\n\n'.join(funcs),
            '(defun c:RUNALL ()\n(INIT)\n%s\n(princ "\\nALL DONE"))' % '\n'.join(calls)]
    with open(out_lisp, 'w', encoding='gbk', errors='replace') as f:
        f.write('; operation sketch generator\r\n')
        f.write('\r\n'.join(code).replace('Ø', 'φ'))
    return out_lisp


def tbl(s, x, y_top, widths, rows, rh=8.0, th=3.0, head=True):
    """Simple ruled table in sheet coordinates (y_top = top line)."""
    total = sum(widths)
    n = len(rows)
    y_bot = y_top - rh * n
    s.set_view(1, 0, 0)
    s.RECT(x, y_bot, x + total, y_top, 'FRAME')
    for i in range(1, n):
        s.L(x, y_top - rh * i, x + total, y_top - rh * i, 'FRAME')
    cx = x
    for w in widths[:-1]:
        cx += w
        s.L(cx, y_bot, cx, y_top, 'FRAME')
    for i, row in enumerate(rows):
        cy = y_top - rh * (i + 0.5)
        cx = x
        for j, txt in enumerate(row):
            s.T(cx + 1.2, cy, th, str(txt), 0, 'TEXT')
            cx += widths[j]
    s.set_view(1, 0, 0)
