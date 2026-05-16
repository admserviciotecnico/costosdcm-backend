'use client';

import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { AuthApi } from '@/lib/api/endpoints';
import { authStore } from '@/stores/auth-store';
import { useRouter } from 'next/navigation';

const schema = z.object({ email: z.string().email(), password: z.string().min(8) });
type FormData = z.infer<typeof schema>;

export default function LoginPage() {
  const setToken = authStore((s) => s.setToken);
  const setUser = authStore((s) => s.setUser);
  const router = useRouter();
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<FormData>({ resolver: zodResolver(schema) });

  const onSubmit = async (data: FormData) => {
    const login = await AuthApi.login(data);
    setToken(login.access_token);
    const me = await AuthApi.me();
    setUser(me);
    router.replace('/dashboard');
  };

  return (
    <div className="min-h-screen grid place-items-center">
      <form onSubmit={handleSubmit(onSubmit)} className="w-full max-w-sm bg-white dark:bg-slate-900 p-6 rounded-xl border border-slate-200 dark:border-slate-800 space-y-4">
        <h1 className="text-2xl font-bold">Iniciar sesión</h1>
        <div>
          <input {...register('email')} placeholder="Email" className="w-full p-2 rounded border" />
          {errors.email && <p className="text-xs text-red-500">{errors.email.message}</p>}
        </div>
        <div>
          <input type="password" {...register('password')} placeholder="Contraseña" className="w-full p-2 rounded border" />
          {errors.password && <p className="text-xs text-red-500">{errors.password.message}</p>}
        </div>
        <button disabled={isSubmitting} className="w-full bg-blue-600 text-white rounded p-2">{isSubmitting ? 'Ingresando...' : 'Entrar'}</button>
      </form>
    </div>
  );
}
