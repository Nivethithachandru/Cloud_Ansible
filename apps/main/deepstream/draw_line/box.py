def callbbox(obj_meta):
    if (obj_meta.class_id == 0):
        obj_meta.rect_params.border_color.set(0.0, 0.0, 0.0, 1.0)
    elif (obj_meta.class_id == 1):
        obj_meta.rect_params.border_color.set(0.0, 0.8, 1.0, 0.0)
    elif (obj_meta.class_id == 2):
        obj_meta.rect_params.border_color.set(0.0, 0.0, 1.0, 1.0)
    elif (obj_meta.class_id == 3):
        obj_meta.rect_params.border_color.set(0.0, 1.0, 0.0, 0.0)
    elif (obj_meta.class_id == 4):
        obj_meta.rect_params.border_color.set(0.0, 1.0, 0.0, 1.0)
    elif (obj_meta.class_id == 5):
        obj_meta.rect_params.border_color.set(0.0, 1.0, 1.0, 0.0)
    elif (obj_meta.class_id == 6):
        obj_meta.rect_params.border_color.set(0.0, 1.0, 1.0, 1.0)
    elif (obj_meta.class_id == 7):
        obj_meta.rect_params.border_color.set(1.0, 0.0, 0.0, 0.0)
    elif (obj_meta.class_id == 8):
        obj_meta.rect_params.border_color.set(1.0, 0.0, 0.0, 1.0)
    elif (obj_meta.class_id == 9):
        obj_meta.rect_params.border_color.set(1.0, 0.0, 1.0, 0.0)
    elif (obj_meta.class_id == 10):
        obj_meta.rect_params.border_color.set(1.0, 0.0, 1.0, 1.0)
    elif (obj_meta.class_id == 11):
        obj_meta.rect_params.border_color.set(1.0, 1.0, 0.0, 0.0)
    elif (obj_meta.class_id == 12):
        obj_meta.rect_params.border_color.set(1.0, 1.0, 0.0, 1.0)
    elif (obj_meta.class_id == 13):
        obj_meta.rect_params.border_color.set(1.0, 1.0, 1.0, 0.0)
    elif (obj_meta.class_id == 14):
        obj_meta.rect_params.border_color.set(1.0, 1.0, 1.0, 1.0)
    elif (obj_meta.class_id == 15):
        obj_meta.rect_params.border_color.set(0.0, 0.0, 0.0, 0.0)

    return obj_meta