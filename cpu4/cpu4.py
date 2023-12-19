from simulator import signals


all_groups = signals.make_groups(2, 2, 1, 4, 1, 1, 1, 1, 4, 4, 1, 1)

(g_a_sel, g_b_sel, g_addr_sel, g_load_sel,
 g_pc_inc, g_mar_inc, g_flags_load, g_mem_en,
 g_aluop_a, g_aluop_b, g_c_sel, g_i_next,
 *others) = all_groups
assert len(others) == 0

a_acc, a_x, a_port, _ = g_a_sel.all()
b_addr0, b_addr1, b_addr2, b_data = g_b_sel.all()
addr_mar, addr_pc = g_addr_sel.all()
(load_ir, load_pc, load_mar, load_mem,
 load_acc, load_x, load_t0, load_t1,
 load_psel, load_port, _, _,
 _, _, _, _) = g_load_sel.all()
_, inc_pc = g_pc_inc.all()
_, inc_mar = g_mar_inc.all()
_, load_flags = g_flags_load.all()
_, mem_en = g_mem_en.all()
c_0, c_1 = g_c_sel.all()
_, i_next = g_i_next.all()

alu_a      = g_aluop_a[0b1010] | g_aluop_b[0b0000] | c_0
alu_b      = g_aluop_a[0b0000] | g_aluop_b[0b1100] | c_0
alu_add    = g_aluop_a[0b1010] | g_aluop_b[0b1100] | c_0
alu_add_c1 = g_aluop_a[0b1010] | g_aluop_b[0b1100] | c_1
alu_sub    = g_aluop_a[0b1010] | g_aluop_b[0b0011] | c_0
alu_nand   = g_aluop_a[0b0110] | g_aluop_b[0b0001] | c_0
alu_xor    = g_aluop_a[0b0110] | g_aluop_b[0b0000] | c_0
alu_nor    = g_aluop_a[0b0000] | g_aluop_b[0b0001] | c_0

next_step = [i_next]
fetch = [addr_pc | mem_en | b_data | alu_b | load_ir | inc_pc]
addr12 = [addr_pc | mem_en | b_data | alu_b | load_t0 | inc_pc,
          addr_pc | mem_en | b_data | alu_b | load_t1 | inc_pc,
          addr_pc | mem_en | b_data | alu_b | load_mar | inc_pc]
addr12_x = [a_x | addr_pc | mem_en | b_data | alu_add | load_t0 | inc_pc,
            addr_pc | mem_en | b_data | alu_b | load_t1 | inc_pc, # not sure how to handle a carry here
            addr_pc | mem_en | b_data | alu_b | load_mar | inc_pc]

STEPS_COUNT = 2**4
NOP = []

def pad(steps, count, op):
    while len(steps) < count:
        steps.append(op)
    return steps

def load(cin):
    def action():
        return pad([], STEPS_COUNT, NOP)
    return action

def store(cin):
    def action():
        return pad([], STEPS_COUNT, NOP)
    return action

# ops = [
#     load, load_indexed, store, store_indexed,
#     jump, jump_indirect, jump_if_carry, jump_if_zero,
#     add, sub, nand, xor,
#     swap_ax, set_port, in, out,
# ]

# op		c	step
