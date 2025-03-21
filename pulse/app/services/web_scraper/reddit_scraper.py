from typing import Any, Sequence

from asyncpraw import Reddit  # type: ignore
from asyncpraw.models import Comment, MoreComments, Submission, SubredditHelper  # type: ignore

from pulse.app.config import PulseConfig, get_config

# from pulse.app.utils.repeat_tasks import repeat_every

config = get_config()


class RedditCrawler:
    def __init__(self, config: PulseConfig, subreddit_names: Sequence[str] = ["wallstreetbets"]) -> None:
        self.reddit_client = Reddit(
            client_id=config.client_id,
            client_secret=config.client_secret,
            user_agent=config.user_agent,
        )

        self.subreddit_names = subreddit_names

    async def scrape_subreddit(self) -> None:
        helper = SubredditHelper(self.reddit_client, None)
        for display in self.subreddit_names:
            subreddit = await helper(display)

            submissions = subreddit.top(time_filter="day")
            submission = await submissions.__anext__()
            count = 0
            async for submission in submissions:
                if count == 2:
                    break
                await self._process_submission(submission)

                count += 1

        print("Scrape Subreddit")

    async def _process_submission(self, submission: Submission) -> None:
        await submission.load()
        await submission.comments.replace_more(limit=0)

        if not submission.comments:
            print(f"No comments loaded for submission {submission.id}")
            return

        raw_comments: list[Comment | MoreComments] = submission.comments.list()  # type: ignore

        valid_comments: list[Comment] = [
            c for c in raw_comments if isinstance(c, Comment) and c.body not in ("[removed]", "[deleted]")
        ]

        sorted_comments: list[Comment] = sorted(
            valid_comments, key=lambda comment: comment.score, reverse=True
        )[:8]

        processed_comments: list[dict[str, Any]] = []
        for comment in sorted_comments:
            if not comment.author:
                continue

            processed_comments.append(
                {
                    "author": comment.author,
                    "score": comment.score,
                    "body": comment.body[:1800],  # Type-safe string slice
                }
            )

        # Final output with type-safe fields
        result: dict[str, Any] = {
            "title": str(submission.title),
            "subreddit": (
                submission.subreddit.display_name
                if hasattr(submission.subreddit, "display_name")
                else str(submission.subreddit)
            ),
            "score": int(submission.score),
            "num_comments": int(submission.num_comments),
            "selftext": (submission.selftext or "")[:2000],  # Handle Optional[str]
            "url": str(submission.url),
            "comments": processed_comments,
        }
        print(result)
