export const COMMAND_DEFINITIONS = [
  {
    commandName: "start-review",
    workflowFile: "feishu-start-review.yml",
    workflowName: "Feishu Start Review",
    description: "Dispatch the Start Review worker on main for one review-init record and force-reseed from the latest template.",
  },
  {
    commandName: "build-draft",
    workflowFile: "feishu-draft-build-queue.yml",
    workflowName: "Feishu Draft Build Queue",
    description: "Dispatch the Build Draft Package worker on main for one Document_link record.",
  },
  {
    commandName: "publish",
    workflowFile: "feishu-build-queue.yml",
    workflowName: "Feishu Build Queue",
    description: "Dispatch the Publish worker on main for one Document_link record after explicit confirmation.",
  },
];
