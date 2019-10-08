import React from 'react';
import ReactDOM from 'react-dom';

const getDisplayName = component => {
    return component.displayName || component.name || "chart";
}

export default function fitWidth(WrappedComponent, withRef = true, minWidth = 100) {
    class ResponsiveComponent extends React.Component {
        constructor() {
            super();
            this.state = {
                width: null
            };
        }

        componentDidMount() {
            window.addEventListener("resize", this.handleWindowResize);
            const el = this.node;
            const w = el.parentNode.clientWidth;
            this.setState({width: w});
        }

        componentWillUnmount() {
            window.removeEventListener("resize", this.handleWindowResize);
        }

        handleWindowResize = () => {
            const el = ReactDOM.findDOMNode(this.node);
            const w = el.parentNode.clientWidth;
            if (w > minWidth)
                this.setState({width: w});
        }

        setNode = node => this.node = node;
        
        getWrappedInstance = () => this.node;

        render() {
            const ref = withRef ? {ref: this.setNode}: {}
            if (this.state.width) {
                return <WrappedComponent 
                    width={this.state.width}
                    {...this.props}
                    {...ref}
                />;
            } else {
                return <div {...ref}></div>;
            }
        }
    };

    ResponsiveComponent.displayName = `fitWidth(${getDisplayName(WrappedComponent)})`;
    return ResponsiveComponent; 
}