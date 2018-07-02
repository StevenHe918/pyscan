import random
from collections import deque, Counter
import bisect
import math
import test_set
import statistics
import itertools
import sampling
import bisect
import heapq
from geometric import approx_eq
from seidel_tree import to_line, Segment, Line, \
    approx_above, approx_eq_above
import poly_tree as poly
import geometric as geom


def stat(m, b):
    if approx_eq(m, 0) and approx_eq(b, 0):
        return 0
    elif approx_eq(b, 0) or approx_eq(b, 1):
        return 0
    elif approx_eq(m, 0):
        return math.log(1 / (1 - b))
    elif approx_eq(m, 1):
        return math.log(1 / b)
    else:
        return m * math.log(m / b) + (1 - m) * math.log((1 - m) / (1 - b))


def order_function(p1, p2):
    y = p2[0] - p1[0]
    x = p2[1] - p1[1]
    if y >= 0:
        return math.atan2(y, x)
    else:
        return math.pi + math.atan2(y, x)

def part_order_function(p1, p2):
    x = p2[0] - p1[0]
    y = p2[1] - p1[1]
    if y >= 0:
        return math.atan2(y, x)
    else:
        return 2 * math.pi + math.atan2(y, x)


class Line3:

    def __init__(self, a, b, c):
        self.a = a
        self.b = b
        self.c = c

    def pt_eq_below_exact(self, pt):
        return self.a * pt[0] + self.b * pt[1] + self.c <= 0

    def pt_eq_below(self, pt):
        return approx_eq_above(self.a * pt[0] + self.b * pt[1] + self.c, 0)

def det2(a1, a2, b1, b2):
    return a1 * b2 - a2 * b1

def det3(p_0, p_1):
    a = det2(p_0[1], 1, p_1[1], 1)
    b = -det2(p_0[0], 1, p_1[0], 1)
    c = det2(p_0[0], p_0[1], p_1[0], p_1[1])
    return a, b, c

def to_line3(pivot, pt):
    if pt[0] - pivot[0] >= 0:
        a, b, c = det3(pivot, pt)
    else:
        a, b, c = det3(pt, pivot)
    return Line3(a, b, c)

def exact_discrepancy(line, red_points, red_weights, blue_points, blue_weights):
    r = sum(w for p, w in zip(red_points, red_weights) if line.pt_eq_below(p))
    b = sum(w for p, w in zip(blue_points, blue_weights) if line.pt_eq_below(p))
    return abs(r / sum(red_weights) - b / sum(blue_weights))

def line_discrepancy(net_sample, red_points, red_weights, blue_points, blue_weights, disc=stat):
    """
    :param big_samp:
    :param small_samp:
    :param weights:
    :param pt_num:
    :param n: The sub-sampling size of the small sample.
    :return:
    """
    #net_sample = random.sample(blue_points, n // 2) + random.sample(red_points, n // 2)
    max_discrepancy = -math.inf
    max_line = Line3(0, 0, 1)
    a = 0
    b = 0
    if red_weights:
        a = 1.0 / sum(red_weights)
    if blue_weights:
        b = 1.0 / sum(blue_weights)

    for i in range(len(net_sample) - 1):
        sample_part = net_sample[i + 1:]

        p_0 = net_sample[i]
        order_f = lambda x: order_function(p_0, x)

        red_delta = [0] * (len(sample_part))
        blue_delta = [0] * (len(sample_part))

        sample_part.sort(key=lambda x: order_f(x))
        angles = [order_f(p) for p in sample_part]
        #all_lines = [to_line3(p_0, p) for p in sample_part]

        l1 = to_line3(p_0, sample_part[0])
        red_curr = 0
        blue_curr = 0
        for p_1, w in zip(red_points, red_weights):

            insertion_pt = bisect.bisect_left(angles, order_f(p_1))
            if insertion_pt == 0 and l1.pt_eq_below(p_1):
                red_curr += w
            else:
                insertion_pt -= 1
                if l1.pt_eq_below(p_1):
                    red_curr += w
                    red_delta[insertion_pt] += -w
                else:
                    red_delta[insertion_pt] += w

        for p_1, w in zip(blue_points, blue_weights):
            insertion_pt = bisect.bisect_left(angles, order_f(p_1))

            if insertion_pt == 0 and l1.pt_eq_below(p_1):
                blue_curr += w
            else:
                insertion_pt -= 1
                if l1.pt_eq_below(p_1):
                    blue_curr += w
                    blue_delta[insertion_pt] += -w
                else:
                    blue_delta[insertion_pt] += w


        red_curr = sum(w for p, w in zip(red_points, red_weights) if l1.pt_eq_below(p))
        blue_curr = sum(w for p, w in zip(blue_points, blue_weights) if l1.pt_eq_below(p))
        # red_curr += red_delta[0]
        # blue_curr += blue_delta[0]
        for db, ds, p_1 in zip(red_delta, blue_delta, sample_part):

            if max_discrepancy <= disc(red_curr * a, blue_curr * b):
                max_line = to_line3(p_0, p_1)
                max_discrepancy = disc(red_curr * a, blue_curr * b)
            # r = sum(w for p, w in zip(red_points, red_weights) if to_line3(p_0, p_1).pt_eq_below(p))
            # b = sum(w for p, w in zip(blue_points, blue_weights) if to_line3(p_0, p_1).pt_eq_below(p))
            # print(r, b, red_curr, blue_curr)
            red_curr += db
            blue_curr += ds


    return max_discrepancy, max_line

class FirstList(list):
    def __lt__(self, other):
        return self[0] < other[0]

def sample_cells(cells, cell_sample_size):
    tw = sum(1 for _ in itertools.chain.from_iterable(cells))

    out_pts = []
    weights = []
    for cell in cells:
        if cell:
            c_size = min(len(cell), int(.5 + round(cell_sample_size)))
            out_pts.extend(random.sample(cell, c_size))
            weights.extend([len(cell) / (float(tw) * c_size)] * c_size)

    return list(out_pts), list(weights)


def random_test_set(pts, t, c=10):
    test_set = []
    for i in range(int(t * t) * c):
        p1, p2 = random.sample(pts, 2)
        test_set.append(to_line(p1, p2))
    return test_set


def partitions(pts, b, min_cell_size=100, cell_sample_size=1, test_set_f=random_test_set):

    cell_queue = [(-len(pts), pts)]
    while True:

        _, curr_pts = heapq.heappop(cell_queue)
        pts_not_in_cells = curr_pts[:]
        test_set = test_set_f(pts_not_in_cells, b)
        weight_map = {line: 1 for line in test_set}
        i = 0
        while len(pts_not_in_cells) > max(len(curr_pts) / b, min_cell_size):
            i += 1
            b_i = max(b / 2**i, 1)

            while len(pts_not_in_cells) > max(len(curr_pts) / (2**i), min_cell_size):
                tree = poly.PolyTree2(pts_not_in_cells, test_set)
                tree.cutting_b(b_i, weight_map)
                cell = tree.get_heaviest()
                for l in cell.get_lines():
                    weight_map[l] *= 2
                lkup = set(cell.get_points())
                pts_not_in_cells = [p for p in pts_not_in_cells if p not in lkup]
                heapq.heappush(cell_queue, FirstList((-len(cell.get_points()), cell.get_points())))
                if len(cell_queue) + 1 >= min(len(pts) / min_cell_size, len(pts)):
                    final_cells = []
                    final_cells.extend([pts for _, pts in cell_queue])
                    final_cells.append(pts_not_in_cells)
                    return sample_cells(final_cells, cell_sample_size)
        heapq.heappush(cell_queue, FirstList((-len(pts_not_in_cells), pts_not_in_cells)))


class BoxCell:

    def __init__(self, pts, lines, lx=-float("inf"), rx=float("inf"), by=-float("inf"), ty=float("inf")):
        self.lx = lx
        self.rx = rx
        self.ty = ty
        self.by = by
        self.pts = pts
        self.lines = lines

    def horz_cut(self, my):
        u_pts = [p for p in self.pts if my < p[1]]
        l_pts = [p for p in self.pts if p[1] <= my]
        u_lines = []
        l_lines = []
        sl = Segment(Line(0, my), self.lx, self.rx)
        u_lines, l_lines= poly.split_lines(sl, self.lines)
        return BoxCell(u_pts, u_lines, self.lx, self.rx, my, self.ty), \
                BoxCell(l_pts, l_lines, self.lx, self.rx, self.by, my)

    def vertical_cut(self, mx):
        r_pts = [p for p in self.pts if mx < p[0]]
        l_pts = [p for p in self.pts if p[0] <= mx]
        l_lines = []
        r_lines =[]
        for l in self.lines:
            y_val = l.evaluate(mx)
            if approx_above(self.by, y_val) and approx_above(y_val, self.ty):
                e1 = Segment(l, l.xl, mx)
                e2 = Segment(l, mx, l.xr)
                l_lines.append(e1)
                r_lines.append(e2)
            elif approx_eq_above(self.ty, y_val):
                if l.a <= 0:
                    r_lines.append(l)
                else:
                    l_lines.append(l)
            else:
                if l.a <= 0:
                    l_lines.append(l)
                else:
                    r_lines.append(l)
        return BoxCell(r_pts, r_lines, mx, self.rx, self.by, self.ty), \
            BoxCell(l_pts, l_lines, self.lx, mx, self.by, self.ty)

    def get_median(self, ix):
        ord_vals = map(lambda x: x[ix], self.pts)
        return statistics.median(ord_vals)

    def get_x_median(self):
        return self.get_median(0)

    def get_y_median(self):
        return self.get_median(1)

    def point_count(self):
        return len(self.pts)

    def get_points(self):
        return self.pts

    def get_lines(self):
        return self.lines

def get_median(pts, ix):
    ord_vals = map(lambda x: x[ix], pts)
    return statistics.median(ord_vals)


def point_cuts(pts,  cell_count, eps=.2):
    """
    Divides the points into sets less than max_number.
    Uses alternating x, y order for the points. By doing this
    we get a set of cells with parameter n^7.9...
    :param pts:
    :param max_number:
    :return:
    """
    cells = []

    cells.append(FirstList((-len(pts), pts)))
    #print(cell_count)
    while len(cells) < cell_count:
        #print(len(out_cells) + len(cells), cell_count)
        _, curr_pts = heapq.heappop(cells)
        if not curr_pts:
            continue
        mv = get_median(curr_pts, 0)
        r_pts = [p for p in curr_pts if mv < p[0]]
        l_pts = [p for p in curr_pts if p[0] <= mv]
        n = int(2 / eps + 1)
        s = int(2 / (eps * eps) + 1)

        #print(len(net_sample))
        #mx_diff = 1
        #mxf = lambda x: abs(len(x) / len(curr_pts) - .25)

        #while mx_diff > eps:
        net_sample = random.sample(r_pts, min(n // 2, len(r_pts))) + random.sample(l_pts, min(n // 2, len(l_pts)))
        r_samp = random.sample(r_pts, min(s, len(r_pts)))
        l_samp = random.sample(l_pts, min(s, len(l_pts)))

        _, l = line_discrepancy(net_sample, r_samp, [1] * len(r_samp), l_samp, [1] * len(l_samp), lambda r, b: 2 - abs(r - .5)**2 - abs(b - .5)**2)
        rl_pts = []
        ru_pts = []
        for p in r_pts:
            if l.pt_eq_below(p):
                rl_pts.append(p)
            else:
                ru_pts.append(p)
        ll_pts = []
        lu_pts = []
        for p in l_pts:
            if l.pt_eq_below(p):
                ll_pts.append(p)
            else:
                lu_pts.append(p)
        # print(len(lu_pts) / len(curr_pts), len(ll_pts) / len(curr_pts), len(rl_pts) / len(curr_pts),
        #       len(ru_pts) / len(curr_pts))

        #mx_diff = max(mxf(lu_pts), mxf(ll_pts), mxf(rl_pts), mxf(ru_pts))

        heapq.heappush(cells, FirstList((-len(rl_pts), rl_pts)))
        heapq.heappush(cells, FirstList((-len(ru_pts), ru_pts)))
        heapq.heappush(cells, FirstList((-len(ll_pts), ll_pts)))
        heapq.heappush(cells, FirstList((-len(lu_pts), lu_pts)))


    return [cp for _, cp in cells]

"""
 TODO Move the poly tree algorithm over here and create a chan version of it.
 
 1) Need to modify the cutting so that the test sets are still internal to each cell. In other
 words the cutting needs to be constrained to the cell above it. (done)
 
 2) Change this so that we compute each cutting with a branching factor of b. This might involve
 doing a search over the cuttings.

3) Test set should be computed with size 1/eps^{4/3} log^{2/3 + 2} 1/eps. Or in other 
words the #cells * log^2(#cells). Or we could construct a sample of points of size 
sqrt(#cells) * log #cells and then feed this into the dual algorithm with r = sqrt(#cells) to get the lines.
This should scale like #cells * log #cells which is the optimal... 

"""



# def chan_partitions(pts, r, min_cell_size=100, cell_sample_size=1,
#                     cutting_f=Pt.compute_cutting,
#                     test_set_f=test_set.test_set_dual_exact_t, c=1, c2=2, max_h=2):
#     b = r * r * c2
#     if max_h is None:
#         max_t = (len(pts) / min_cell_size)
#         max_h = len(pts)
#     else:
#         max_t = int(b ** (max_h) + .1)
#
#     active_levels = deque()
#     active_levels.append(pts)
#     final_cells = []
#
#     while active_levels:
#         curr_pts = active_levels.pop()
#         if len(curr_pts) <= min_cell_size:
#             final_cells.append(curr_pts)
#             continue
#         test_set_size = int(max_t * (math.log(max_t) ** 2) * c + .5)
#         print(test_set_size)
#         test_set = test_set_f(curr_pts, test_set_size)
#         curr_level = [(curr_pts, test_set)]
#         t = 1
#         for i in range(max_h):
#             max_part_size = max(2 * len(curr_pts) / (t * b), 1)
#             print(max_part_size)
#             curr_level, finished_cells = find_light_cells(curr_level, min_cell_size)
#             final_cells.extend(finished_cells)
#             if curr_level:
#                 curr_level = chan_process_level(curr_level, max_part_size, test_set, cutting_f, r)
#             else:
#                 break
#             t *= b
#         for cell_pts, _ in curr_level:
#             active_levels.append(cell_pts)
#     return sample_cells(final_cells, cell_sample_size)



def chan_partitions_simple2(pts, b, min_cell_size=100):

    import test_set
    final_cells = []

    n = (len(pts) / min_cell_size)
    line_test_set = test_set.test_set_dual(pts, int(n+1))
    tree = poly.PolyTree2(points=pts, lines=line_test_set)
    weight_map = {}
    for l in line_test_set:
        weight_map[l] = 1
    curr_level = [(tree.root, None)]

    t = 1
    while curr_level:
        active_level = []
        waiting_level = []
        for curr_root, parent in curr_level:
            if len(curr_root.get_points()) <= min_cell_size:
                if len(curr_root.get_points()) > 0:
                    final_cells.append((curr_root, parent))
                #final_cells.append((curr_root, parent))
            elif len(pts) / t <= len(curr_root.get_points()):
                active_level.append((curr_root, parent))
            else:
                waiting_level.append((curr_root, parent))


        # ensure that the active level is processed in a random order
        random.shuffle(active_level)


        for l in weight_map:
            weight_map[l] = 1

        cell_count = len(waiting_level) + len(active_level) + len(final_cells)
        curr_level = []
        for curr_root, parent in active_level:

            sub_partitions = tree.cutting_b(b / 2, weight_map, curr_root, parent)
            sub_cells = []
            # Cut each node of the sub-tree into sub-cells containing at most 2n/(tb) points.
            part_size = max(2 * len(pts) / (t * b), min_cell_size)
            #print("t = {} Psz = {} b = {} psz = {} lsz = {} wsz={}".format(t, part_size, len(sub_partitions), len(curr_pts), len(t_s), sum(weight_map[l] for l in t_s)))
            for cell, parent in sub_partitions:
                cell_list = tree.partition(cell, parent, part_size)
                sub_cells.extend(cell_list)

            cell_count += sum(1 for cell, _ in sub_cells if len(cell.get_points()) > 0) - 1
            if cell_count >= n:
                return tree
            # Compute the count of line crossings
            l_counts = Counter()
            for sub_cell, _ in sub_cells:
                l_counts.update(sub_cell.get_lines())
            # Apply re-weighting operation
            for l in l_counts:
                weight_map[l] *= (1 + 1.0 / len(sub_partitions)) ** (l_counts[l])

            curr_level.extend(sub_cells)
        curr_level.extend(waiting_level)
        t *= 2

    return tree


def chan_partitions_simple(pts, b=24, min_cell_size=100):


    n = (len(pts) / min_cell_size)
    #line_test_set = test_set.test_set_dual(pts, int(n+1))
    line_test_set = test_set.test_set_points(pts, n)
    tree = poly.PolyTree2(points=pts, lines=line_test_set)

    curr_level = [(tree.root, None)]

    while True:
        weight_map = {}
        for l in line_test_set:
            weight_map[l] = 1


        #active_level = sampling.weighted_shuffle(curr_level, [len(r.get_points()) / len(pts) for r, _ in curr_level])
        #active_level = sampling.weighted_shuffle(curr_level, [len(r.total_weight(weight_map)) / len(pts) for r, _ in curr_level])
        active_level = curr_level[:]
        random.shuffle(active_level)
        curr_level = []
        cell_count = len(active_level)
        t = cell_count
        for curr_root, parent in active_level:

            sub_cells = []
            if len(curr_root.get_points()) <= min_cell_size:
                sub_cells.append((curr_root, parent))
                # final_cells.append((curr_root, parent))
            else:
                sub_partitions = tree.cutting_b(b / 2, weight_map, curr_root, parent)
                # Cut each node of the sub-tree into sub-cells containing at most 2n/(tb) points.
                part_size = max(2 * len(pts) / (t * b), min_cell_size)
                #print("t = {} Psz = {} b = {} psz = {} lsz = {} wsz={}".format(t, part_size, len(sub_partitions), len(curr_pts), len(t_s), sum(weight_map[l] for l in t_s)))
                for cell, parent in sub_partitions:
                    cell_list = tree.partition(cell, parent, part_size)
                    sub_cells.extend([(c, p) for c, p in cell_list if len(c.get_points()) > 0])

                cell_count += len(sub_cells) - 1
                if cell_count >= n:
                    return tree
                # Compute the count of line crossings
                l_counts = Counter()
                for sub_cell, _ in sub_cells:
                    l_counts.update(sub_cell.get_lines())
                # Apply re-weighting operation
                for l in l_counts:
                    weight_map[l] *= (1 + 1.0 / len(sub_cells)) ** (l_counts[l])

            curr_level.extend(sub_cells)


def test_set_power(b, t, n, m):
    return -int(-round(math.log(math.sqrt(b) * math.log(n) / m, 2) + .5))


def cell_rate(b, t, n, m):
    return min(math.sqrt(b) * math.log(n) / math.sqrt(t), .9)




class segment_search:

    def __init__(self, pts):

        self.angle_orders = []
        self.pts = pts
        self.lines = []
        for i in range(len(pts) - 1):
            pt = pts[i]
            pt_order = pts[:i] + pts[(i + 1):]
            pt_order.sort(key=lambda x: part_order_function(pt, x))
            angle_order = []
            lines = []
            for j in range(len(pt_order)):
                try:
                    l = to_line(pt, pt_order[j])
                except ZeroDivisionError:
                    continue
                angle_order.append(part_order_function(pt, pt_order[j]))
                lines.append(l)
            self.angle_orders.append(angle_order)
            self.lines.append(lines)


    def get_line_crossing(self, segment):

        def pt_angle(pt, segment):
            if math.isinf(segment.left_vertex[1]):
                l_angle = part_order_function((0, 0), (-1, segment.a))
            else:
                l_angle = part_order_function(pt, segment.left_vertex)
            if segment.right_vertex[1] == math.inf:
                r_angle = part_order_function((0, 0), (1, segment.a))
            else:
                r_angle = part_order_function(pt, segment.right_vertex)
            return l_angle, r_angle

        def get_lines(pt, angle_order, l_angle, r_angle, lines):
            if segment.crossed_by_segment(Segment(Line(0, pt[1]), pt[0], math.inf)):
                bottom_angle = max(l_angle, r_angle)
                top_angle = min(l_angle, r_angle)
                return lines[bisect.bisect_left(angle_order, bottom_angle):] + lines[:bisect.bisect_right(angle_order, top_angle)]
            else:
                top_angle = max(l_angle, r_angle)
                bottom_angle = min(l_angle, r_angle)
                return lines[bisect.bisect_left(angle_order, bottom_angle):bisect.bisect_right(angle_order, top_angle)]


        def same_pt(p1, p2):
            return geom.approx_eq(p1[0], p2[0]) and geom.approx_eq(p1[1], p2[1])

        out_lines = []
        for i, pt, angle_order in zip(range(len(self.pts)), self.pts, self.angle_orders):
            if same_pt(pt, segment.left_vertex):
                out_lines.extend(self.lines[i])
            elif same_pt(pt, segment.right_vertex):
                out_lines.extend(self.lines[i])
            else:
                l_a, r_a = pt_angle(pt, segment)
                out_lines.extend(get_lines(pt, angle_order, l_a, r_a, self.lines[i]))

        return out_lines

    def get_lines_crossing_poly(self, polygon):
        all_lines = []
        for seg in polygon.get_border_lines():
            all_lines.extend(self.get_line_crossing(seg))
        return geom.deduplicate_points(all_lines)


    def get_all_lines(self):
        return list(itertools.chain(*self.lines))


def chan_partitions2(pts, b, min_cell_size=100, c=2):

    n = len(pts)
    s = n / min_cell_size

    tree = poly.PolyTree2(points=pts)

    d_pts = random.sample(pts, 2)
    curr_level = [(tree.root, None)]
    lines_in_tree = set()
    curr_test_set_power = 0
    r_hat = []
    t = 1
    while True:
        d_pts = random.sample(pts, max(int(math.sqrt(t) * math.log(t) - len(d_pts) + .5), 10)) + d_pts
        segment_struct = segment_search(d_pts)
        line_test_set = segment_struct.get_all_lines()

        m = len(line_test_set)
        p = 2.0 ** test_set_power(b, t, n, m)
        if curr_test_set_power != test_set_power(b, t, n, m):
            curr_test_set_power = test_set_power(b, t, n, m)
            p = 2.0 ** curr_test_set_power
            r_hat = list(sampling.p_sample(line_test_set, p))
            for l in r_hat:
                if l not in lines_in_tree:
                    lines_in_tree.add(l)
                    tree.add_line(l)


        weight_map = {l: 1 for l in line_test_set}
        r_weight_map = {l: 0 for l in line_test_set}
        for l in r_hat:
            r_weight_map[l] = 1

        #active_level = curr_level[:]
        active_level = curr_level[:]
        random.shuffle(active_level)
        #active_level = sampling.weighted_shuffle(curr_level, [len(r.total_weight(r_weight_map)) / len(pts) for r, _ in curr_level])
        random.shuffle(active_level)
        curr_level = []
        cell_count = len(active_level)
        for curr_root, parent in active_level:
            sub_cells = []

            if len(pts) / t <= len(curr_root.get_points()):
                sub_partitions = tree.cutting_b(b / c, r_weight_map, curr_root, parent)
                # Cut each node of the sub-tree into sub-cells containing at most 2n/(tb) points.
                part_size = max(2 * len(pts) / (t * b), min_cell_size)
                #print("t = {} Psz = {} b = {} psz = {}, lsz={}".format(t, part_size, len(sub_partitions), len(curr_root.get_points()), len(curr_root.get_lines())))
                for cell, parent in sub_partitions:
                    cell_list = tree.partition(cell, parent, part_size)
                    sub_cells.extend([(c, p) for c, p in cell_list if len(c.get_points()) > 0])


                cell_count += len(sub_cells) - 1

                if cell_count >= s:
                    return tree
                # 3
                # Sample the cells of this decomposition and then count the lines inside of them.
                l_counts = Counter()
                for sub_cell, _ in sub_cells:
                    if random.random() < cell_rate(b, t, n, m):
                        new_lines = segment_struct.get_lines_crossing_poly(sub_cell)
                        l_counts.update(new_lines)

                # 3(a) and 3(b)
                for l in l_counts:
                    try:
                        old_weight = weight_map[l]
                        weight_map[l] *= (1 + 1.0 / len(sub_cells)) ** (l_counts[l])

                        #simulates taking a sample from the newly added lines
                        k = sampling.binom_rand_k(weight_map[l] - old_weight, p)
                        if k > 0:
                            # add these newly sampled lines to the r_weight_map
                            r_weight_map[l] += k
                            if l not in lines_in_tree:
                                lines_in_tree.add(l)
                                tree.add_line(l)
                    except KeyError:
                        continue
            else:
                sub_cells.append((curr_root, parent))
            curr_level.extend(sub_cells)
        if len(pts) / t <= min_cell_size:
            return tree

        t *= 2



def quadTreeSample(pts, min_cell_size=100, cell_sample_size=1):
    s = min(len(pts)/ min_cell_size, len(pts))
    boxes = point_cuts(pts, cell_count=s)
    return sample_cells([b for b in boxes], cell_sample_size)



if __name__ == "__main__":
    import matplotlib.pyplot as plt
    import matplotlib
    import partitioning_tests
    import line_testing
    pts = partitioning_tests.upload_crimes("crimes.csv")

    pts = random.sample(pts, 100000)

    matplotlib.rcParams['figure.figsize'] = [20.0, 20.0]


    tree = chan_partitions2(pts, b = 28, min_cell_size=100)

    f, ax = plt.subplots()
    s_pts = random.sample(pts, 10000)
    x, y = zip(*pts)
    ax.scatter(x, y, marker='.')

    tree.visualize_arrangement(ax, min(x), max(x), min(y), max(y))
    plt.show()
    
    
# if __name__ == "__main__":
#     import matplotlib.pyplot as plt
#     import matplotlib
#     import partitioning_tests
#     #pts = partitioning_tests.upload_crimes("crimes.csv")
# #
#     pts = [(random.random(), random.random()) for i in range(1000000)]
#     quadTreeSample(pts)
#     segment_class = segment_search(pts)
#     lines = segment_class.get_all_lines()
#
#     segment = Segment(to_line(pts[0], pts[1]), pts[0][0], pts[1][0])
#     small_lines = segment_class.count_segment(segment)
#     f, ax = plt.subplots()
#     min_x = 0
#     max_x = 1
#     min_y = 0
#     max_y = 1
#
#     for l in lines:
#          poly.visualize_line(ax, l, min_x, max_x, min_y, max_y, "r", .5)
#
#     for l in small_lines:
#         poly.visualize_line(ax, l, min_x, max_x, min_y, max_y, "b", .5)
#
#     poly.visualize_edge(ax, segment, min_x, max_x, min_y, max_y, "k", 5)
#
#     matplotlib.rcParams['figure.figsize'] = [20.0, 20.0]
#     #tree = chan_partitions2(pts, 128)
#     #s_pts = random.sample(pts, 10000)
#     #x, y = zip(*s_pts)
#     #ax.scatter(x, y, marker='.')
#     #tree.visualize_arrangement(ax, 0, 1, 0, 1)
#     ax.set_ylim([0, 1])
#     ax.set_xlim([0, 1])
#     plt.show()


#random_sample_time_plot2(999, 1000, 100000, 10)
#print("got here")
#time_plot2(200, 10000, 1000000, 20, r=2, c=.1)
#error_plot_output_size(100000, 100, 800, 10, r=2)
#random_sample_plot(100000, 200, 1200, 20)
#random_error_plot(10000, 20, 200, 20, r=2048, c=.1)
#random_error_plot2(10000, 200, 1, 10, 20, r=2048, c=.1)
#random_sample_time_plot(10000, 50, 1000, 100)