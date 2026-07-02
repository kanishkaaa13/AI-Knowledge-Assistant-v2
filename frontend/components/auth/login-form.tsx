"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { Loader2 } from "lucide-react";

import { useAuth } from "@/components/providers/auth-provider";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
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
    } catch (error: any) {
      let detail = error?.response?.data?.detail 
        || (error instanceof Error ? error.message : null) 
        || (typeof error === "string" ? error : null);
      let message = "Unable to log in.";

      if (detail === "User not found") {
        message = "User not found";
      } else if (detail === "Incorrect password") {
        message = "Incorrect password";
      } else if (detail === "Account inactive") {
        message = "Account inactive";
      } else if (detail) {
        message = typeof detail === "string" ? detail : JSON.stringify(detail);
      }

      setError("password", { type: "server", message });
      toast.error(message);
    }
  };

  return (
    <form className="space-y-5" onSubmit={handleSubmit(onSubmit)}>
      <div className="space-y-2">
        <Label htmlFor="email">Email</Label>
        <Input id="email" placeholder="you@example.com" {...register("email")} />
        {errors.email ? <p className="text-sm text-red-500">{errors.email.message}</p> : null}
      </div>

      <div className="space-y-2">
        <Label htmlFor="password">Password</Label>
        <Input id="password" type="password" placeholder="Enter your password" {...register("password")} />
        {errors.password ? (
          <p className="text-sm text-red-500">{errors.password.message}</p>
        ) : null}
      </div>

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

