export const parseFuncName = name => {
    const prefix = (name+"([").match(/.+?(?=[\[\(])/)[0];
    return prefix.match(/(.*::)*(.*)/)[2];    
}

export const getRandomColor = () => {
    return {
        r: Math.floor(Math.random() * 255),
        g: Math.floor(Math.random() * 255),
        b: Math.floor(Math.random() * 255)
    }
};
