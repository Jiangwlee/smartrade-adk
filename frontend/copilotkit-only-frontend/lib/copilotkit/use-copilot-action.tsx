"use client";

import { useCopilotAction } from "@copilotkit/react-core"

export function useCopilotActionRenderer() {
  useCopilotAction({
    name: "sayHello",
    description: "Say hello to the user",
    available: "remote", // optional, makes it so the action is *only* available to the agent
    parameters: [
      {
        name: "name",
        type: "string",
        description: "The name of the user to say hello to",
        required: true,
      },
    ],
    handler: async ({ name }) => {
      alert(`Hello, ${name}!`);
    },
  });
}