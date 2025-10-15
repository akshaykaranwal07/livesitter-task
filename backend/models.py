# simple schema hints (not enforced)
OVERLAY_SCHEMA = {
'name': str,
'type': str, # 'text' | 'image'
'content': str,
'x': (int, float), # 0-100 percent
'y': (int, float),
'width': (int, float),
'height': (int, float),
'zIndex': int,
'visible': bool
}