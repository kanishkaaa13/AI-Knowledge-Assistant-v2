"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { Loader2 } from "lucide-react";

import { AuthFormField } from "@/components/auth/auth-form-field";
import { useAuth } from "@/components/providers/auth-provider";
import { extractErrorMessage } from "@/lib/errors";
import { Button } from "@/components/ui/button";
import { loginSchema, type LoginSchema } from "@/lib/validations/auth";

export function LoginForm() {
  const { loginUser } = useAuth();
  const searchParams = useSearchParams();
  const {
    register,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting }
  } = useForm<LoginSchema>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: "",
      password: ""
    }
  });

  const onSubmit = async (values: LoginSchema) => {
    const redirectTo = searchParams.get("redirect") || "/dashboard";

    try {
      await loginUser(values, redirectTo);
    } catch (error: unknown) {
      const message = extractErrorMessage(error, "Unable to log in.");

      setError("password", { type: "server", message });
      toast.error(message);
    }
  };

  return (
    <form className="space-y-5" onSubmit={handleSubmit(onSubmit)}>
      <AuthFormField
        error={errors.email?.message}
        label="Email"
        name="email"
        placeholder="you@example.com"
        registration={register("email")}
      />

      <AuthFormField
        error={errors.password?.message}
        label="Password"
        name="password"
        placeholder="Enter your password"
        registration={register("password")}
        type="password"
      />

      <Button className="w-full" size="lg" type="submit" disabled={isSubmitting}>
        {isSubmitting ? (
          <>
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            Signing in...
          </>
        ) : (
          "Sign in"
        )}
      </Button>

      <p className="text-sm text-muted-foreground">
        Need an account?{" "}
        <Link className="font-medium text-primary" href="/register">
          Create one
        </Link>
      </p>
    </form>
  );
}

