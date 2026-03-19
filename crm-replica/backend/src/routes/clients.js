import { Router } from 'express';
import { prisma } from '../config/prisma.js';
import { authRequired, requireRole } from '../middleware/auth.js';
import { validateBody } from '../middleware/validation.js';
import { clientCreateSchema, clientUpdateSchema } from '../services/schemas.js';

const router = Router();
router.use(authRequired);

router.get('/', async (_req, res) => {
  const items = await prisma.client.findMany({ where: { is_active: true, deleted_at: null }, orderBy: { created_at: 'desc' } });
  res.json(items);
});

router.post('/', requireRole('admin'), validateBody(clientCreateSchema), async (req, res) => {
  res.status(201).json(await prisma.client.create({ data: req.body }));
});

router.patch('/:id', requireRole('admin'), validateBody(clientUpdateSchema), async (req, res) => {
  res.json(await prisma.client.update({ where: { id: req.params.id }, data: req.body }));
});

router.delete('/:id', requireRole('admin'), async (req, res) => {
  const hasActiveOrders = await prisma.serviceOrder.count({ where: { client_id: req.params.id, is_active: true, deleted_at: null } });
  if (hasActiveOrders > 0) return res.status(400).json({ message: 'Cannot delete client with active orders' });

  await prisma.client.update({ where: { id: req.params.id }, data: { is_active: false, deleted_at: new Date() } });
  res.json({ ok: true });
});

export default router;
