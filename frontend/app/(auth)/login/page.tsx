import { AuthRedirect } from "@/components/auth/auth-redirect";
import { AuthFormShell } from "@/components/auth/auth-form-shell";
import { LoginForm } from "@/components/auth/login-form";

export default function LoginPage() {
  return (
    <AuthRedirect>
      <AuthFormShell
        title="Welcome back"
        description="Sign in to continue into your AI knowledge workspace."
        footer="Your session uses secure cookie-based JWT authentication with automatic refresh support."
      >
        <LoginForm />
      </AuthFormShell>
    </AuthRedirect>
  );
}
