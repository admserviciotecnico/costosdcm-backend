import { Router } from 'express';
import { prisma } from '../config/prisma.js';
import { authRequired, requireRole } from '../middleware/auth.js';
import { validateBody } from '../middleware/validation.js';
import { equipmentCreateSchema, equipmentUpdateSchema } from '../services/schemas.js';

const router = Router();
router.use(authRequired);

router.get('/', async (_req, res) => {
  const items = await prisma.equipment.findMany({ where: { is_active: true, deleted_at: null }, orderBy: { created_at: 'desc' } });
  res.json(items);
});

router.post('/', requireRole('admin'), validateBody(equipmentCreateSchema), async (req, res) => {
  res.status(201).json(await prisma.equipment.create({ data: req.body }));
});

router.patch('/:id', requireRole('admin'), validateBody(equipmentUpdateSchema), async (req, res) => {
  res.json(await prisma.equipment.update({ where: { id: req.params.id }, data: req.body }));
});

router.delete('/:id', requireRole('admin'), async (req, res) => {
  await prisma.equipment.update({ where: { id: req.params.id }, data: { is_active: false, deleted_at: new Date() } });
  res.json({ ok: true });
});

export default router;
