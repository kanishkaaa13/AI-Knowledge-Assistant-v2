"use client";

import { ChevronDown, LogOut, Settings2 } from "lucide-react";

import { useAuth } from "@/components/providers/auth-provider";
import { ThemeToggle } from "@/components/ui/theme-toggle";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger
} from "@/components/ui/dropdown-menu";
import { Button } from "@/components/ui/button";

export function ProfileDropdown({
  onOpenSettings
}: {
  onOpenSettings: () => void;
}) {
  const { logoutUser, user } = useAuth();

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button className="w-full justify-start rounded-2xl" variant="secondary">
          <span className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/10 text-primary">
            {user?.name?.slice(0, 1).toUpperCase() ?? "A"}
          </span>
          <span className="hidden text-left sm:block">
            <span className="block text-sm font-medium">{user?.name ?? "Account"}</span>
          </span>
          <ChevronDown className="h-4 w-4" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-64">
        <DropdownMenuLabel>Profile</DropdownMenuLabel>
        <div className="px-3 pb-2 text-sm text-muted-foreground">
          <p className="font-medium text-foreground">{user?.name}</p>
          <p>{user?.email}</p>
        </div>
        <DropdownMenuSeparator />
        <div className="px-3 py-2">
          <div className="flex items-center justify-between rounded-2xl bg-secondary px-3 py-2">
            <span className="text-sm">Theme</span>
            <ThemeToggle />
          </div>
        </div>
        <DropdownMenuItem onClick={onOpenSettings}>
          <Settings2 className="mr-2 h-4 w-4" />
          Settings
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => void logoutUser()}>
          <LogOut className="mr-2 h-4 w-4" />
          Log out
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
