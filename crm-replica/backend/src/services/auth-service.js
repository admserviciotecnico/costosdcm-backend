import crypto from 'crypto';

export function hashPassword(password) {
  return crypto.createHash('sha256').update(password).digest('hex');
}

export function registerUser({ users, first_name, last_name, email, password, role = 'tecnico' }) {
  if (users.some((u) => u.email === email)) throw new Error('EMAIL_EXISTS');
  const user = {
    id: crypto.randomUUID(),
    first_name,
    last_name,
    email,
    role,
    password: hashPassword(password)
  };
  users.push(user);
  return { id: user.id, email: user.email };
}

export function loginUser({ users, email, password }) {
  const user = users.find((u) => u.email === email);
  if (!user) throw new Error('INVALID_CREDENTIALS');
  if (user.password !== hashPassword(password)) throw new Error('INVALID_CREDENTIALS');
  return { access_token: `test-token-${user.id}`, token_type: 'bearer', sub: user.id };
}
