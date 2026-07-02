"use client";

type Resolver<TInput, TOutput> = {
  input: TInput;
  resolve: (value: TOutput) => void;
  reject: (reason?: unknown) => void;
};

export function createRequestBatcher<TInput, TOutput>({
  batchDelay = 25,
  execute
}: {
  batchDelay?: number;
  execute: (inputs: TInput[]) => Promise<TOutput[]>;
}) {
  let queue: Resolver<TInput, TOutput>[] = [];
  let timer: number | null = null;

  async function flush() {
    const pending = queue;
    queue = [];
    timer = null;

    try {
      const results = await execute(pending.map((item) => item.input));
      pending.forEach((entry, index) => entry.resolve(results[index]));
    } catch (error) {
      pending.forEach((entry) => entry.reject(error));
    }
  }

  return (input: TInput) =>
    new Promise<TOutput>((resolve, reject) => {
      queue.push({ input, resolve, reject });
      if (timer !== null) {
        return;
      }
      timer = window.setTimeout(() => {
        void flush();
      }, batchDelay);
    });
}
