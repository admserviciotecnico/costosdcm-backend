function sanitizeValue(value) {
  if (typeof value === 'string') {
    return value.replace(/[<>]/g, '').trim();
  }
  if (Array.isArray(value)) return value.map(sanitizeValue);
  if (value && typeof value === 'object') {
    const out = {};
    Object.entries(value).forEach(([k, v]) => {
      out[k] = sanitizeValue(v);
    });
    return out;
  }
  return value;
}

export function sanitizeBody(req, _res, next) {
  req.body = sanitizeValue(req.body ?? {});
  next();
}
