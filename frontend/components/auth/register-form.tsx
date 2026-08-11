"use client";

import Link from "next/link";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { toast } from "sonner";

import { AuthFormField } from "@/components/auth/auth-form-field";
import { useAuth } from "@/components/providers/auth-provider";
import { extractErrorMessage } from "@/lib/errors";
import { Button } from "@/components/ui/button";
import { registerSchema, type RegisterSchema } from "@/lib/validations/auth";

export function RegisterForm() {
  const { registerUser } = useAuth();
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting }
  } = useForm<RegisterSchema>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      name: "",
      email: "",
      password: ""
    }
  });

  const onSubmit = async (values: RegisterSchema) => {
    try {
      await registerUser(values);
    } catch (error: unknown) {
      toast.error(extractErrorMessage(error, "Unable to create your account."));
    }
  };

  return (
    <form className="space-y-5" onSubmit={handleSubmit(onSubmit)}>
      <AuthFormField
        error={errors.name?.message}
        label="Name"
        name="name"
        placeholder="Alex Johnson"
        registration={register("name")}
      />

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
        placeholder="Create a strong password"
        registration={register("password")}
        type="password"
      />

      <Button className="w-full" size="lg" type="submit" disabled={isSubmitting}>
        {isSubmitting ? "Creating account..." : "Create account"}
      </Button>

      <p className="text-sm text-muted-foreground">
        Already have an account?{" "}
        <Link className="font-medium text-primary" href="/login">
          Sign in
        </Link>
      </p>
    </form>
  );
}
