# encoding: utf-8
# module pay_load
"""
    Soft-model for payload control
"""


class PayLoad_11:
    def __init__(self, lm=None):
        self.voltage = 0
        self.current = 0
        self.power = 0
        self.temperature = 0
        self.output_state = 0
        self.input_state = 0
        self.lm = lm  # чеерез данный объект происходит общение с модулем сопряжения
        self.pl_type = "_A"
        pass

    def set_out(self, rst_fpga=True, rst_leon=True):
        rst_fpga_int = 1 if rst_fpga else 0
        rst_leon_int = 1 if rst_leon else 0
        output_state = ((rst_leon_int & 0x01) << 1) | ((rst_fpga_int & 0x01) << 0)
        if self.pl_type is "_A":
            self.lm.send_cmd_reg(mode="pl11_a_outputs", data=[output_state])
        elif self.pl_type is "_B":
            self.lm.send_cmd_reg(mode="pl11_b_outputs", data=[output_state])

    def send_data(self, uint32_addr=None, uint32_word=None):

        pass

    def get_out_int(self, mode="int"):
        interrupt = 0

        return interrupt