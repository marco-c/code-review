# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import structlog

from code_review_bot import Issue
from code_review_bot import Level
from code_review_bot.tasks.base import AnalysisTask

logger = structlog.get_logger(__name__)

ISSUE_MARKDOWN = """
## infer error

- **Message**: {message}
- **Location**: {location}
- **In patch**: {in_patch}
- **Infer check**: {check}
- **Publishable **: {publishable}
"""


class InferIssue(Issue):
    """
    An issue reported by infer
    """

    def __init__(self, analyzer, entry, revision):
        assert isinstance(entry, dict)
        kind = entry.get("kind") or entry.get("severity")
        assert kind is not None, "Missing issue kind"
        super().__init__(
            analyzer,
            revision,
            path=entry["file"],
            line=entry["line"],
            nb_lines=1,
            check=entry["bug_type"],
            column=entry["column"],
            level=Level.Warning,
            message=entry["qualifier"],
        )

    def validates(self):
        """
        Publish infer issues all the time
        """
        return True

    def as_text(self):
        """
        Build the text body published on reporters
        """
        message = self.message
        if len(message) > 0:
            message = message[0].capitalize() + message[1:]
        return "{}: {} [infer: {}]".format(self.level.name, message, self.check)

    def as_markdown(self):
        return ISSUE_MARKDOWN.format(
            check=self.check,
            message=self.message,
            location="{}:{}:{}".format(self.path, self.line, self.column),
            in_patch="yes" if self.revision.contains(self) else "no",
            publishable="yes" if self.is_publishable() else "no",
        )


class InferTask(AnalysisTask):
    """
    Support remote Infer analyzer
    """

    artifacts = ["public/code-review/infer.json"]

    def build_help_message(self, files):
        files = " ".join(files)
        return f"`./mach static-analysis check-java {files} (Java)"

    def parse_issues(self, artifacts, revision):
        """
        Parse issues from a direct Infer JSON report
        """
        assert isinstance(artifacts, dict)
        return [
            InferIssue(analyzer=self, revision=revision, entry=issue)
            for issues in artifacts.values()
            for issue in issues
        ]
