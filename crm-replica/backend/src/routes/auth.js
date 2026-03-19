import { Router } from 'express';
import bcrypt from 'bcryptjs';
import jwt from 'jsonwebtoken';
import { prisma } from '../config/prisma.js';
import { env } from '../config/env.js';
import { authRequired } from '../middleware/auth.js';
import { validateBody } from '../middleware/validation.js';
import { rateLimit } from '../middleware/rate-limit.js';
import { loginSchema, registerSchema } from '../services/schemas.js';

const router = Router();
const authLimiter = rateLimit({ windowMs: 60_000, max: 15 });

router.post('/register', authLimiter, validateBody(registerSchema), async (req, res) => {
  const role = await prisma.role.findUnique({ where: { name: req.body.role } });
  const hashed = await bcrypt.hash(req.body.password, 10);
  const user = await prisma.user.create({ data: { ...req.body, password: hashed, role_id: role.id } });
  res.status(201).json({ id: user.id, email: user.email });
});

router.post('/login', authLimiter, validateBody(loginSchema), async (req, res) => {
  const user = await prisma.user.findUnique({ where: { email: req.body.email }, include: { role: true } });
  if (!user || !(await bcrypt.compare(req.body.password, user.password))) return res.status(401).json({ message: 'Invalid credentials' });
  const access_token = jwt.sign({ sub: user.id, role: user.role.name, email: user.email }, env.jwtSecret, { expiresIn: env.jwtExpiresIn });
  res.json({ access_token, token_type: 'bearer' });
});

router.get('/me', authRequired, async (req, res) => {
  const { password, ...safe } = req.user;
  res.json({ ...safe, role: req.user.role.name });
});

export default router;
