import {
  CopilotKit,
  useCopilotAction,
} from "@copilotkit/react-core";
import { CopilotPopup } from "@copilotkit/react-ui";
import "@copilotkit/react-ui/styles.css";
import { ReactNode } from "react";
import { useAppState } from "../lib/state/app-state";
import {
  isNavigationDestination,
  NAVIGATION_DESTINATIONS,
} from "./navigation";

function CopilotNavigationAction() {
  const { setActiveTab } = useAppState();

  useCopilotAction(
    {
      name: "navigate_nexvora",
      description:
        "Navigate to one of the available NexVora application sections. Use only the exact destination values listed in the parameter description.",
      parameters: [
        {
          name: "destination",
          type: "string",
          description: NAVIGATION_DESTINATIONS.join(", "),
          required: true,
        },
      ],
      handler: async ({ destination }: { destination: string }) => {
        if (!isNavigationDestination(destination)) {
          throw new Error("Unsupported NexVora navigation destination.");
        }

        setActiveTab(destination);
        return `Navigated to ${destination}.`;
      },
    },
    [setActiveTab],
  );

  return null;
}

type CopilotIntegrationProps = {
  children: ReactNode;
};

export function CopilotIntegration({
  children,
}: CopilotIntegrationProps) {
  const enabled = import.meta.env.VITE_COPILOTKIT_ENABLED === "true";
  const runtimeUrl = import.meta.env.VITE_COPILOT_RUNTIME_URL?.trim();

  if (!enabled || !runtimeUrl) {
    return <>{children}</>;
  }

  return (
    <CopilotKit runtimeUrl={runtimeUrl}>
      <CopilotNavigationAction />
      {children}
      <CopilotPopup
        labels={{
          title: "NexVora Copilot",
          initial: "How can I help you navigate NexVora?",
        }}
      />
    </CopilotKit>
  );
}
