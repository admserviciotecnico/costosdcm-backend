import jwt from 'jsonwebtoken';
import { env } from '../config/env.js';
import { prisma } from '../config/prisma.js';

export async function authRequired(req, res, next) {
  const auth = req.headers.authorization;
  if (!auth?.startsWith('Bearer ')) return res.status(401).json({ message: 'Unauthorized' });
  try {
    const payload = jwt.verify(auth.slice(7), env.jwtSecret);
    const user = await prisma.user.findUnique({ where: { id: payload.sub }, include: { role: true } });
    if (!user || !user.active) return res.status(401).json({ message: 'Unauthorized' });
    req.user = user;
    next();
  } catch {
    return res.status(401).json({ message: 'Unauthorized' });
  }
}

export function requireRole(...roles) {
  return (req, res, next) => {
    if (!req.user || !roles.includes(req.user.role.name)) {
      return res.status(403).json({ message: 'Forbidden' });
    }
    next();
  };
}
