from PIL import Image, ImageDraw

def render_annotated_overlay(sketch_img, sketch_pts, measured_payload, show_target=True, show_learner=True):
    base = sketch_img.convert("RGBA")
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    w, h = base.size

    x_left, x_right = int(sketch_pts["face_left"][0] * w), int(sketch_pts["face_right"][0] * w)
    pad = int((x_right - x_left) * 0.18)
    line_x1, line_x2 = max(10, x_left - pad), min(w - 10, x_right + pad)

    feature_map = {"eye_line_vertical": "eye_line", "nose_to_chin_third": "nose_base", "mouth_lower_ratio": "mouth"}
    for idx, err in enumerate(measured_payload["top_priority_errors"], start=1):
        fid = err["feature_id"]
        if fid not in feature_map: continue
        pt_key = feature_map[fid]
        actual_y, target_y = int(sketch_pts[pt_key][1] * h), int(err["sketch_target_y_norm"] * h)

        if show_target:
            for x in range(line_x1, line_x2, 16):
                draw.line([(x, target_y), (min(x + 10, line_x2), target_y)], fill=(16, 185, 129, 230), width=3)
        if show_learner:
            color = (239, 68, 68, 230) if err["status"] == "needs_adjustment" else (245, 158, 11, 230)
            draw.line([(line_x1, actual_y), (line_x2, actual_y)], fill=color, width=3)
            badge_x = line_x2 - 24
            draw.line([(badge_x, actual_y), (badge_x, target_y)], fill=color, width=3)
            draw.ellipse([(badge_x-14, actual_y-14), (badge_x+14, actual_y+14)], fill=color, outline=(255,255,255,255), width=2)
            draw.text((badge_x-4, actual_y-7), str(idx), fill=(255,255,255,255))

    return Image.alpha_composite(base, overlay).convert("RGB")