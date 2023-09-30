# OPENASSISTENT_30B_XOR = "OpenAssistant/oasst-sft-6-llama-30b-xor"
from dataclasses import dataclass


META_70B_HF = "meta-llama/Llama-2-70b-chat-hf"
CODELLAMA_34B_HF = "codellama/CodeLlama-34b-Instruct-hf"
FALCON_180B = "tiiuae/falcon-180B-chat"


@dataclass
class Prompt:
    """
    This is the base prompt class.
    You can use it as default prompt.
    !!! This prompt can only be used once in each conversation !!!
    """

    system: str = ""
    user: str = ""
    _prefix: str = ""

    def toText(self) -> str:
        p = self._prefix
        p += f"System: {self.system}\n"
        p += f"User: {self.user}"
        return p


@dataclass
class PromptFalcon(Prompt):
    """
    Prompt for `falcon` in huggingface.co/chat.
    Extend class<Prompt> and inject `system prompt` with prefix.
    !!! This prompt can only be use once in each conversation !!!
    """

    _prefix: str = "None\nFalcon:\n"


@dataclass
class PromptLlama(Prompt):
    """
    Prompt for `meta-llama & codellama` in huggingface.co/chat.
    Extend class<Prompt> and inject `system prompt` with prefix.
    !!! This prompt can only be use once in each conversation !!!
    """

    _prefix: str = "  [/INST]  </s>\n\n"

    def toText(self) -> str:
        return (
            self._prefix + f"<s>[INST] <<SYS>>{self.system}\n\n<</SYS>>\n\n{self.user}"
        )
