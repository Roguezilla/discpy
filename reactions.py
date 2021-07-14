from typing import Dict, List


class MessageReactions:
    def __init__(self, reactions: List[Dict]):
        self.__reactions = reactions

    def get_count(self, emoji: Dict):
        for r in self.__reactions:
            if r['emoji'] == emoji:
                return r['count']