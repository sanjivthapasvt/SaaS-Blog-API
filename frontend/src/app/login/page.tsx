import { LoginForm } from '@/components/login-form';

export default function LoginPage() {
  return (
    <section>
      <h1>Sign in</h1>
      <p>Use your API account credentials to store JWT tokens locally for testing authenticated endpoints.</p>
      <LoginForm />
    </section>
  );
}
