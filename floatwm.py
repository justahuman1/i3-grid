import i3

DISPLAY_MONITORS = {
    "eDP1",
    "HDMI1",
}

# class FloatManager:


class FloatUtils:
    def __init__(self):
        self.area_matrix, self.current_display = self._calc_metadata()
        pass

    def _calc_metadata(self):
        displays = i3.get_outputs()
        total_size = [[], []]
        for display in displays:
            if display['name'] not in DISPLAY_MONITORS:
                continue
            total_size[0] += [display['rect']['width']]
            total_size[1] += [display['rect']['height']]
        active = [i for i in i3.get_workspaces() if i['focused']]
        print(active)

        return total_size, active

    def current_display(self):
        socket = i3.Socket()

if __name__ == "__main__":
    print(i3)
    # div = 4
