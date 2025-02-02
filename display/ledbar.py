import ledshim
ledshim.set_clear_on_exit()

def update(temperature):
    v = temperature % 10
    (r, g, b) = (255, 255, 255)
    if temperature < 0:
        (r, g, b) = (0, 0, 255)
    elif temperature < 10:
        (r, g, b) = (0, 255, 0)
    elif temperature < 20:
        (r, g, b) = (0, 255, 255)
    elif temperature > 20:
        (r, g, b) = (255, 255, 0)

    try:
        for x in range(ledshim.NUM_PIXELS):
            if x > v:
                r, g, b = 0, 0, 0
            else:
                r, g, b = [int(min(v, 1.0) * c) for c in [r, g, b]]

            ledshim.set_pixel(x, r, g, b)
            ledshim.show()
    except Exception:
        print("Failed to display on ledshim")