"""Summary."""
import os
import sys
from typing import Dict, Generator, List, Tuple, Union

import graphviz
import yaml


def format_component(config: Dict[str, Union[None, str, List[str]]]) -> Tuple[str, str]:
    """Summary.

    Args:
        config (Dict[str, Union[None, str, List[str]]]): Description

    Returns:
        Tuple[str, str]: Description
    """
    return (f'component_{config.get("name")}', f'<<table border="0" cellborder="0"><tr><td bgcolor="#0071BD">{config.get("name")}</td></tr></table>>')


def format_topic(typestr: str, config: Dict[str, Union[None, str, List[str]]]) -> Generator[Tuple[str, str], None, None]:
    """Summary.

    Args:
        typestr (str): Description
        config (Dict[str, Union[None, str, List[str]]]): Description

    Yields:
        Generator[Tuple[str, str], None, None]: Description
    """
    tlist = config.get(typestr) or []
    if isinstance(tlist, str):
        tlist = [tlist]

    for topic_element in tlist:
        topic_str = '.'.join(sorted('&#x3a;'.join(topic_element.split(':')).split('.')))
        yield (f'topic_{topic_str}', topic_str)


def load_configs(folders: List[str]) -> List[Dict[str, Union[None, str, List[str]]]]:
    """Summary.

    Args:
        folders (List[str]): Description

    Returns:
        List[Dict[str, Union[None, str, List[str]]]]: Description
    """
    configs = []

    for folder in folders:
        for name in list_paths(folder):
            try:
                with open(f'{folder}/{name}/{name}.yaml', 'r', encoding='utf8') as stream:
                    config = yaml.safe_load(stream)
                    config['name'] = name
                    configs.append(config)
            except FileNotFoundError:
                pass
    return configs


def topics(dot: graphviz.Digraph, configs: List[Dict[str, Union[None, str, List[str]]]]) -> None:  # type: ignore[no-any-unimported]
    """Summary.

    Args:
        dot (graphviz.Digraph): Description
        configs (List[Dict[str, Union[None, str, List[str]]]]): Description
    """
    dot.attr('node', shape='none')

    for config in configs:
        for topic_element in format_topic('pubtopic', config):
            dot.edge(format_component(config)[0], topic_element[0])
            dot.node(*topic_element)
        for topic_element in format_topic('subtopic', config):
            dot.node(*topic_element)
            dot.edge(topic_element[0], format_component(config)[0])


def derived_topics(dot: graphviz.Digraph, configs: List[Dict[str, Union[None, str, List[str]]]]) -> None:  # type: ignore[no-any-unimported]
    """Summary.

    Args:
        dot (graphviz.Digraph): Description
        configs (List[Dict[str, Union[None, str, List[str]]]]): Description
    """
    for pub in configs:
        for sub in configs:
            for pub_topic in format_topic('pubtopic', pub):
                for sub_topic in format_topic('subtopic', sub):
                    if sub_topic[0] == pub_topic[0]:
                        continue

                    if all(topic_element in pub_topic[1].split('.') for topic_element in sub_topic[1].split('.')):
                        dot.edge(pub_topic[0], sub_topic[0])


def components(dot: graphviz.Digraph, configs: List[Dict[str, Union[None, str, List[str]]]]) -> None:  # type: ignore[no-any-unimported]
    """Summary.

    Args:
        dot (graphviz.Digraph): Description
        configs (List[Dict[str, Union[None, str, List[str]]]]): Description
    """
    dot.attr('node', shape='circle', width='1', color='#ffffff80', penwidth='2', fixedsize='true')

    for config in configs:
        dot.node(*format_component(config))


def graph(folders: List[str]) -> None:  # pylint: disable=too-many-branches
    """Summary.

    Args:
        folders (List[str]): Description
    """
    configs: List[Dict[str, Union[None, str, List[str]]]] = load_configs(folders)

    dot = graphviz.Digraph(comment='Component Diagram')
    dot.attr('graph', bgcolor='#0071BD', nodesep='1')
    dot.attr('edge', color='#ffffff80')
    dot.attr('node', fontcolor='#ffffff', fontname='arial')

    components(dot, configs)
    topics(dot, configs)
    derived_topics(dot, configs)

    dot.render('.ergo.gv', view=True)


def list_paths(path: str) -> List[str]:
    """Summary.

    Args:
        path (str): Description

    Returns:
        List[str]: Description
    """
    ret = []
    for file in os.listdir(path):
        directory = os.path.join(path, file)
        if os.path.isdir(directory):
            ret.append(file)
    return ret


if __name__ == '__main__':
    graph(sys.argv[1:])
