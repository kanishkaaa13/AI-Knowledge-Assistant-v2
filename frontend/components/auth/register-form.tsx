"use client";

import Link from "next/link";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { toast } from "sonner";

import { useAuth } from "@/components/providers/auth-provider";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
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
    } catch (error: any) {
      const detail = error?.response?.data?.detail 
        || (error instanceof Error ? error.message : null) 
        || (typeof error === "string" ? error : null);
      
      const message = detail 
        ? (typeof detail === "string" ? detail : JSON.stringify(detail)) 
        : "Unable to create your account.";
        
      toast.error(message);
    }
  };

  return (
    <form className="space-y-5" onSubmit={handleSubmit(onSubmit)}>
      <div className="space-y-2">
        <Label htmlFor="name">Name</Label>
        <Input id="name" placeholder="Alex Johnson" {...register("name")} />
        {errors.name ? <p className="text-sm text-red-500">{errors.name.message}</p> : null}
      </div>

      <div className="space-y-2">
        <Label htmlFor="email">Email</Label>
        <Input id="email" placeholder="you@example.com" {...register("email")} />
        {errors.email ? <p className="text-sm text-red-500">{errors.email.message}</p> : null}
      </div>

      <div className="space-y-2">
        <Label htmlFor="password">Password</Label>
        <Input id="password" type="password" placeholder="Create a strong password" {...register("password")} />
        {errors.password ? (
          <p className="text-sm text-red-500">{errors.password.message}</p>
        ) : null}
      </div>

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
