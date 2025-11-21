import data from '../data/tree.json' assert { type: 'json' };

const container = document.getElementById('tree-view');

function renderNode(node, indent = 0) {
  const wrapper = document.createElement('div');
  wrapper.className = 'tree-node';
  wrapper.style.paddingLeft = `${indent * 16}px`;

  const title = document.createElement('div');
  title.className = 'tree-node-title';
  title.textContent = node.name;

  const meta = document.createElement('div');
  meta.className = 'tree-node-meta';
  const parts = [];
  if (node.description) parts.push(node.description);
  if (node.recommendation) parts.push(`<span class="tree-tip">${node.recommendation}</span>`);
  if (node.path) parts.push(`<code>${node.path}</code>`);
  meta.innerHTML = parts.join(' ');

  wrapper.appendChild(title);
  wrapper.appendChild(meta);

  if (node.steps && node.steps.length) {
    const steps = document.createElement('div');
    steps.className = 'tree-steps';
    steps.innerHTML = `<strong>How to use:</strong><ul>${node.steps.map(step => `<li>${step}</li>`).join('')}</ul>`;
    wrapper.appendChild(steps);
  }

  if (node.children && node.children.length) {
    node.children.forEach(child => wrapper.appendChild(renderNode(child, indent + 1)));
  }

  return wrapper;
}

container.textContent = '';
data.forEach(node => container.appendChild(renderNode(node)));
