from jinja2 import Environment, FileSystemLoader
import yaml

def render_agent_spec(memo: dict, version: str, templates_dir: str):
    env = Environment(
        loader=FileSystemLoader(templates_dir),
        autoescape=False,
        trim_blocks=True,
        lstrip_blocks=True
    )

    sys_template = env.get_template("agent_system_prompt.j2")
    system_prompt = sys_template.render(**memo)

    spec_template = env.get_template("agent_spec.yaml.j2")
    rendered = spec_template.render(
        **memo,
        system_prompt=system_prompt,
        version=version
    )

    yaml.safe_load(rendered)  # validate
    return rendered