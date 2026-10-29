def compute_proportion_deltas(ref_pts, sketch_pts):
    def normalize(pts):
        h = pts["chin"][1] - pts["crown"][1]
        w = pts["face_right"][0] - pts["face_left"][0]
        return {k: [(v[0] - pts["face_left"][0])/w if w!=0 else v[0], 
                    (v[1] - pts["crown"][1])/h if h!=0 else v[1]] for k, v in pts.items()}

    ref_norm = normalize(ref_pts)
    sketch_norm = normalize(sketch_pts)
    
    features = {"eye_line_vertical": "eye_line", "nose_to_chin_third": "nose_base", "mouth_lower_ratio": "mouth"}
    errors = []
    for fid, pt_key in features.items():
        target_y, actual_y = ref_norm[pt_key][1], sketch_norm[pt_key][1]
        delta = actual_y - target_y
        errors.append({"feature_id": fid, "delta_pct": delta * 100, "sketch_target_y_norm": target_y, 
                       "status": "needs_adjustment" if abs(delta) > 0.035 else "on_target"})
    
    top_errors = sorted(errors, key=lambda x: abs(x["delta_pct"]), reverse=True)[:3]
    return {"top_priority_errors": top_errors, "all_metrics": errors}