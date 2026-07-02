import { AuthRedirect } from "@/components/auth/auth-redirect";
import { AuthFormShell } from "@/components/auth/auth-form-shell";
import { RegisterForm } from "@/components/auth/register-form";

export default function RegisterPage() {
  return (
    <AuthRedirect>
      <AuthFormShell
        title="Create your account"
        description="Register to start managing sources, conversations, and assistant workflows."
        footer="Passwords are hashed with bcrypt on the backend before they ever reach the database."
      >
        <RegisterForm />
      </AuthFormShell>
    </AuthRedirect>
  );
}
