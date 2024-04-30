"""
Upload script called by Github Actions
"""

import sys
from aind_behavior_curriculum import (
    export_curriculum
)

# YOUR CURRICULUM HERE!
USER_CURRICULUM = None

if __name__ == '__main__':
    if not (USER_CURRICULUM is None):
        # Github Actions uploads contents of tmp_dir to S3
        tmp_dir = sys.argv[1]
        export_curriculum(USER_CURRICULUM, tmp_dir)